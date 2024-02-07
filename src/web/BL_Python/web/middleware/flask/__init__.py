import re
import uuid
from logging import Logger
from typing import Awaitable, Callable, Dict, TypeVar
from uuid import uuid4

import json_logging
from connexion import FlaskApp
from flask import Flask, Request, Response, request
from flask.typing import (
    AfterRequestCallable,
    BeforeRequestCallable,
    ResponseReturnValue,
)
from injector import inject

from ...config import Config
from ..consts import (
    CONTENT_SECURITY_POLICY_HEADER,
    CORRELATION_ID_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER,
    HOST_HEADER,
    INCOMING_REQUEST_MESSAGE,
    ORIGIN_HEADER,
    OUTGOING_RESPONSE_MESSAGE,
    REQUEST_COOKIE_HEADER,
    RESPONSE_COOKIE_HEADER,
)

# pyright: reportUnusedFunction=false


# Fixes type problems when using @inject with @app.before_request and @app.after_request.
# The main difference with these types as opposed to the Flask-defined types is that
# these types allow the handler to take any arguments, versus no arguments or just Response.
AfterRequestCallable = Callable[..., Response] | Callable[..., Awaitable[Response]]
BeforeRequestCallable = (
    Callable[..., ResponseReturnValue | None]
    | Callable[..., Awaitable[ResponseReturnValue | None]]
)
T_request_callable = TypeVar(
    "T_request_callable", bound=BeforeRequestCallable | AfterRequestCallable | None
)
# Fixes type problems when using Flask-Injector, which automatically sets up any bound
# error handlers. The error handler types in Flask have the same problem as After/BeforeRequestCallable
# in that their parameters are `[Any]` rather than `...`. This relaxes that. The type
# is valid here because Flask-Injector does actually include the provided types as parameters.
ErrorHandlerCallable = (
    Callable[..., ResponseReturnValue] | Callable[..., Awaitable[ResponseReturnValue]]
)
T_error_handler = TypeVar("T_error_handler", bound=ErrorHandlerCallable)

TFlaskApp = Flask | FlaskApp
T_flask_app = TypeVar("T_flask_app", bound=TFlaskApp)


def bind_requesthandler(
    app: T_flask_app,
    flask_app_handler: Callable[
        [T_flask_app, Callable[..., Response | None]], T_request_callable
    ],
):
    def wrapper(request_callable: Callable[..., Response | None]) -> T_request_callable:
        return flask_app_handler(app, request_callable)

    return wrapper


def _get_correlation_id(log: Logger) -> str:
    correlation_id = _get_correlation_id_from_json_logging(log)

    if not correlation_id:
        correlation_id = _get_correlation_id_from_headers(log)

    return correlation_id


def _get_correlation_id_from_headers(log: Logger) -> str:
    try:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)

        if correlation_id:
            # validate format
            _ = uuid.UUID(correlation_id)
        else:
            correlation_id = str(uuid4())
            log.info(
                f'Generated new UUID "{correlation_id}" for {CORRELATION_ID_HEADER} request header.'
            )

        return correlation_id

    except ValueError as e:
        log.warning(f"Badly formatted {CORRELATION_ID_HEADER} received in request.")
        raise e


def _get_correlation_id_from_json_logging(log: Logger) -> str | None:
    correlation_id: None | str
    try:
        correlation_id = json_logging.get_correlation_id(request)
        # validate format
        _ = uuid.UUID(correlation_id)
        return correlation_id
    except ValueError as e:
        log.warning(f"Badly formatted {CORRELATION_ID_HEADER} received in request.")
        raise e
    except Exception as e:
        log.debug(
            f"Error received when getting {CORRELATION_ID_HEADER} header from `json_logging`. Possibly `json_logging` is not configured, and this is not an error.",
            exc_info=e,
        )


@inject
def _log_all_api_requests(
    request: Request,
    config: Config,
    log: Logger,
):
    request_headers_safe: dict[str, str] = dict(request.headers)

    correlation_id = _get_correlation_id(log)

    if (
        request_headers_safe.get(REQUEST_COOKIE_HEADER)
        and config.flask
        and config.flask.session
    ):
        request_headers_safe[REQUEST_COOKIE_HEADER] = re.sub(
            rf"({config.flask.session.cookie.name}=)[^;]+(;|$)",
            r"\1<redacted>\2",
            request_headers_safe[REQUEST_COOKIE_HEADER],
        )

    log.info(
        INCOMING_REQUEST_MESSAGE,
        request.method,
        request.url,
        request.host,
        request.remote_addr,
        request.remote_user,
        extra={
            "props": {
                "correlation_id": correlation_id,
                "headers": request_headers_safe,
            }
        },
    )


@inject
def _ordered_api_response_handers(response: Response, config: Config, log: Logger):
    _wrap_all_api_responses(response, config, log)
    _log_all_api_responses(response, config, log)
    return response


def _wrap_all_api_responses(response: Response, config: Config, log: Logger):
    correlation_id = _get_correlation_id(log)

    cors_domain: str | None = None
    if config.web.security.cors.origin:
        cors_domain = config.web.security.cors.origin
    else:
        if not response.headers.get(CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER):
            cors_domain = request.headers.get(ORIGIN_HEADER)
            if not cors_domain:
                cors_domain = request.headers.get(HOST_HEADER)

    if cors_domain:
        response.headers[CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER] = cors_domain

    response.headers[CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER] = str(
        config.web.security.cors.allow_credentials
    )

    response.headers[CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER] = ",".join(
        config.web.security.cors.allow_methods
    )

    response.headers[CORRELATION_ID_HEADER] = correlation_id

    if config.web.security.csp:
        response.headers[CONTENT_SECURITY_POLICY_HEADER] = config.web.security.csp

    # if config.flask and config.flask.openapi and config.flask.openapi.use_swagger:
    #    # Use a permissive CSP for the Swagger UI
    #    # https://github.com/swagger-api/swagger-ui/issues/7540
    #    FIXME what to use other than `request` w/ Connexion middleware?
    #    if request.path.startswith("/ui/") or (
    #        request.url_rule and request.url_rule.endpoint == "/v1./v1_swagger_ui_index"
    #    ):
    #        response.headers[
    #            CONTENT_SECURITY_POLICY_HEADER
    #        ] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; script-src 'self' 'unsafe-inline'"


def _log_all_api_responses(response: Response, config: Config, log: Logger):
    correlation_id = _get_correlation_id(log)

    response_headers_safe: Dict[str, str] = dict(response.headers)

    if (
        response_headers_safe.get(RESPONSE_COOKIE_HEADER)
        and config.flask
        and config.flask.session
    ):
        response_headers_safe[RESPONSE_COOKIE_HEADER] = re.sub(
            rf"({config.flask.session.cookie.name}=)[^;]+(;|$)",
            r"\1<redacted>\2",
            response_headers_safe[RESPONSE_COOKIE_HEADER],
        )

    log.info(
        OUTGOING_RESPONSE_MESSAGE,
        response.status_code,
        response.status,
        extra={
            "props": {
                "correlation_id": correlation_id,
                "headers": response_headers_safe,
            }
        },
    )


def register_flask_api_request_handlers(app: Flask):
    return bind_requesthandler(app, Flask.before_request)(_log_all_api_requests)


def register_flask_api_response_handlers(app: Flask):
    # TODO consider moving request/response logging to the WSGI app
    # apparently Flask may not call this if unhandled exceptions occur
    return bind_requesthandler(app, Flask.after_request)(_ordered_api_response_handers)
