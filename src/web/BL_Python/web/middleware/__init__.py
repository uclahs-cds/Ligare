import json
import re
import uuid
from logging import Logger
from typing import Awaitable, Callable, Dict, TypeVar
from uuid import uuid4

import json_logging
from flask import Flask, Request, Response, request
from flask.typing import (
    AfterRequestCallable,
    BeforeRequestCallable,
    ResponseReturnValue,
)
from flask_injector import FlaskInjector
from injector import Module, inject
from werkzeug.exceptions import HTTPException, Unauthorized

from ..config import Config
from .dependency_injection import AppModule

CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_COOKIE_HEADER = "Cookie"
RESPONSE_COOKIE_HEADER = "Set-Cookie"
CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER = "Access-Control-Allow-Origin"
CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER = "Access-Control-Allow-Credentials"
CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER = "Access-Control-Allow-Methods"
CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy"
ORIGIN_HEADER = "Origin"
HOST_HEADER = "Host"

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


def bind_requesthandler(
    app: Flask,
    flask_app_handler: Callable[
        [Flask, Callable[..., Response | None]], T_request_callable
    ],
):
    def wrapper(request_callable: Callable[..., Response | None]) -> T_request_callable:
        return flask_app_handler(app, request_callable)

    return wrapper


def bind_errorhandler(
    app: Flask,
    code_or_exception: type[Exception] | int,
) -> Callable[[T_error_handler], T_error_handler]:
    return app.errorhandler(code_or_exception)


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


INCOMING_REQUEST_MESSAGE = "Incoming request:\n\
    %s %s\n\
    Host: %s\n\
    Remote address: %s\n\
    Remote user: %s"

OUTGOING_RESPONSE_MESSAGE = f"Outgoing response:\n\
   Status code: %s\n\
   Status: %s"


def register_api_request_handlers(app: Flask):
    @bind_requesthandler(app, Flask.before_request)
    @inject
    def log_all_api_requests(request: Request, config: Config, log: Logger):
        correlation_id = _get_correlation_id(log)

        request_headers_safe: Dict[str, str] = dict(request.headers)

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


def register_api_response_handlers(app: Flask):
    # TODO consider moving request/response logging to the WSGI app
    # apparently Flask may not call this if unhandled exceptions occur
    @bind_requesthandler(app, Flask.after_request)
    @inject
    def ordered_api_response_handers(response: Response, config: Config, log: Logger):
        wrap_all_api_responses(response, config, log)
        log_all_api_responses(response, config, log)
        return response

    def wrap_all_api_responses(response: Response, config: Config, log: Logger):
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

        if config.flask and config.flask.openapi and config.flask.openapi.use_swagger:
            # Use a permissive CSP for the Swagger UI
            # https://github.com/swagger-api/swagger-ui/issues/7540
            if request.path.startswith("/ui/") or (
                request.url_rule
                and request.url_rule.endpoint == "/v1./v1_swagger_ui_index"
            ):
                response.headers[
                    CONTENT_SECURITY_POLICY_HEADER
                ] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; script-src 'self' 'unsafe-inline'"

    def log_all_api_responses(response: Response, config: Config, log: Logger):
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


def register_error_handlers(app: Flask):
    @bind_errorhandler(app, Exception)
    def catch_all_catastrophic(error: Exception, log: Logger):
        log.exception(error)

        response = {
            "status_code": 500,
            "error_msg": "Unknown error.",
            "status": "Internal Server Error",
        }
        return response, 500

    @bind_errorhandler(app, HTTPException)
    def catch_all(error: HTTPException, log: Logger):
        log.exception(error)

        response = {
            "status_code": error.code,
            "error_msg": error.description,
            "status": error.name,
        }

        return (
            response,
            error.code if error.code is not None else 500,
        )

    @bind_errorhandler(app, 401)
    def unauthorized(error: Unauthorized, log: Logger):
        log.info(error)

        if error.response is None or not isinstance(error.response, Response):
            response = {
                "status_code": 401,
                "error_msg": error.description,
                "status": error.name,
            }
            return response, 401

        response = error.response
        data = {
            "status_code": response.status_code,
            "error_msg": response.data.decode(),
            "status": response.status,
        }
        response.data = json.dumps(data)
        return response


def configure_dependencies(
    app: Flask,
    application_modules: list[Module] | None = None,
):
    """
    Configures dependency injection and registers all Flask
    application dependencies. The FlaskInjector instance
    can be used to bootstrap and start the Flask application.
    """
    modules = [AppModule(app)] + (application_modules if application_modules else [])

    # bootstrap the flask application and its dependencies
    flask_injector = FlaskInjector(app, modules)

    return flask_injector
