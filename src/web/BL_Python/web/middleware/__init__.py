import json
import re
from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    MutableMapping,
    TypeVar,
    Union,
    cast,
)
from uuid import uuid4

import json_logging
from flask import Flask  # pyright: ignore[reportGeneralTypeIssues]
from flask import Request, Response, request, session
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
HEADER_COOKIE = "Cookie"

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


def bind(
    app: Flask,
    flask_app_handler: Callable[
        [Flask, Callable[..., Response | None]], T_request_callable
    ],
):
    def wrapper(request_callable: Callable[..., Response | None]) -> T_request_callable:
        return flask_app_handler(app, request_callable)

    return wrapper


def _get_correlation_id(log: Logger):
    _session = cast(MutableMapping[str, str], session)
    try:
        _session[CORRELATION_ID_HEADER] = json_logging.get_correlation_id(request)
        return _session[CORRELATION_ID_HEADER]
    except Exception as e:
        correlation_id = _session.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid4())
            session[CORRELATION_ID_HEADER] = correlation_id
            log.warning(
                f'`json_logging` not configured. Generated new UUID "{correlation_id}" for request correlation ID. Error: "{e}"'
            )
        return correlation_id


def register_api_request_handlers(app: Flask):
    @bind(app, Flask.before_request)
    @inject
    def log_all_api_requests(request: Request, config: Config, log: Logger):
        correlation_id = _get_correlation_id(log)

        request_headers_safe: Dict[str, str] = dict(request.headers)

        if (
            request_headers_safe.get(HEADER_COOKIE)
            and config.flask
            and config.flask.session
        ):
            request_headers_safe[HEADER_COOKIE] = re.sub(
                rf"({config.flask.session.cookie.name}=)[^;]+(;|$)",
                r"\1<redacted>\2",
                request_headers_safe[HEADER_COOKIE],
            )

        log.info(
            f"Incoming request:\n\
    {request.method} {request.url}\n\
    Host: {request.host}\n\
    Remote address: {request.remote_addr}\n\
    Remote user: {request.remote_user}",
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
    @bind(app, Flask.after_request)
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
            if not response.headers.get("Access-Control-Allow-Origin"):
                cors_domain = request.headers.get("Origin")
                if not cors_domain:
                    cors_domain = request.headers.get("Host")

        if cors_domain:
            response.headers["Access-Control-Allow-Origin"] = cors_domain

        response.headers["Access-Control-Allow-Credentials"] = str(
            config.web.security.cors.allow_credentials
        )

        response.headers["Access-Control-Allow-Methods"] = ",".join(
            config.web.security.cors.allow_methods
        )

        response.headers[CORRELATION_ID_HEADER] = correlation_id

        if config.web.security.csp:
            response.headers["Content-Security-Policy"] = config.web.security.csp

        if config.flask and config.flask.openapi and config.flask.openapi.use_swagger:
            # Use a permissive CSP for the Swagger UI
            # https://github.com/swagger-api/swagger-ui/issues/7540
            if request.path.startswith("/ui/") or (
                request.url_rule
                and request.url_rule.endpoint == "/v1./v1_swagger_ui_index"
            ):
                response.headers[
                    "Content-Security-Policy"
                ] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; script-src 'self' 'unsafe-inline'"

    def log_all_api_responses(response: Response, config: Config, log: Logger):
        correlation_id = _get_correlation_id(log)

        response_headers_safe: Dict[str, str] = dict(response.headers)

        if (
            response_headers_safe.get(HEADER_COOKIE)
            and config.flask
            and config.flask.session
        ):
            response_headers_safe[HEADER_COOKIE] = re.sub(
                rf"(Set-Cookie: {config.flask.session.cookie.name}=)[^;]+(;|$)",
                r"\1<redacted>\2",
                response_headers_safe[HEADER_COOKIE],
            )

        log.info(
            f"Outgoing response:\n\
   Status code: {response.status_code}\n\
   Status: {response.status}",
            extra={
                "props": {
                    "correlation_id": correlation_id,
                    "headers": response_headers_safe,
                }
            },
        )


def register_error_handlers(app: Flask):
    @app.errorhandler(Exception)
    def catch_all_catastrophic(error: Exception, log: Logger):
        log.exception(error)

        response = {"status_code": 500, "error_msg": "Unknown error."}
        return response, 500

    @app.errorhandler(HTTPException)
    def catch_all(error: HTTPException, log: Logger):
        log.exception(error)

        response = {
            "status_code": error.code,
            "error_msg": error.description,
            "status": error.name,
        }
        return response, error.code

    @app.errorhandler(401)
    def unauthorized(
        error: Unauthorized, log: Logger
    ) -> Union[Dict[str, int], Response]:
        log.info(error)

        if error.response is None:
            response = {
                "status_code": error.code,
                "error_msg": error.description,
                "status": error.name,
            }
            return response, error.code  # pyright: ignore[reportGeneralTypeIssues]

        response = error.response
        data = {
            "status_code": response.status_code,
            "error_msg": response.data.decode(),
            "status": response.status,
        }
        response.data = json.dumps(data)
        return response  # pyright: ignore[reportGeneralTypeIssues]


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
