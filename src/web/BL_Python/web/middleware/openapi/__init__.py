import re
import uuid
from logging import Logger
from typing import Any, Awaitable, Callable, Literal, TypeVar, cast
from uuid import uuid4

import json_logging
from BL_Python.programming.collections.dict import AnyDict
from connexion import ConnexionMiddleware, FlaskApp, utils
from flask import Flask, Response
from flask.typing import (
    AfterRequestCallable,
    BeforeRequestCallable,
    ResponseReturnValue,
)
from injector import inject
from starlette.types import ASGIApp, Receive, Scope, Send
from typing_extensions import TypedDict

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


MiddlewareRequestDict = TypedDict(
    "MiddlewareRequestDict",
    {
        "type": Literal["http"],
        "http_version": str,
        "method": Literal[
            "GET",
            "POST",
            "PATCH",
            "PUT",
            "DELETE",
            "OPTIONS",
            "HEAD",
            "CONNECT",
            "TRACE",
        ],
        "path": str,
        "raw_path": bytes,
        "root_path": str,
        "scheme": str,
        "query_string": bytes,
        "headers": list[tuple[bytes, bytes]],
        "client": list[
            str | int
        ],  # this is actually a 2-item list whose first item is a str and second item is an int
        "server": list[str | int],  # same here
        "extensions": dict[str, dict[str, str]],
        "state": AnyDict,
        "app": ConnexionMiddleware,
        "starlette.exception_handlers": tuple[
            dict[type[Any], Callable[..., Any]], dict[Any, Any]
        ],
        "path_params": dict[Any, Any],
    },
)

MiddlewareResponseDict = TypedDict(
    "MiddlewareResponseDict",
    {
        "type": Literal["http.response.start"],
        "status": int,
        "headers": list[tuple[bytes, bytes]],
    },
)


def _get_correlation_id(
    request: MiddlewareRequestDict, response: MiddlewareResponseDict, log: Logger
) -> str:
    correlation_id = _get_correlation_id_from_json_logging(response, log)

    if not correlation_id:
        correlation_id = _get_correlation_id_from_headers(request, response, log)

    return correlation_id


def _get_correlation_id_from_headers(
    request: MiddlewareRequestDict, response: MiddlewareResponseDict, log: Logger
) -> str:
    try:
        headers = _headers_as_dict(request)
        correlation_id = headers.get(CORRELATION_ID_HEADER.lower())

        if not correlation_id:
            headers = _headers_as_dict(response)
            correlation_id = headers.get(CORRELATION_ID_HEADER.lower())

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


def _get_correlation_id_from_json_logging(
    request_response: MiddlewareRequestDict | MiddlewareResponseDict, log: Logger
) -> str | None:
    correlation_id: None | str
    try:
        correlation_id = json_logging.get_correlation_id(request_response)
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


def _headers_as_dict(
    request_response: MiddlewareRequestDict | MiddlewareResponseDict,
):
    if (
        isinstance(
            request_response, dict
        )  # pyright: ignore[reportUnnecessaryIsInstance]
        and "headers" in request_response.keys()
    ):
        # FIXME does this work for a middleware _response_ as well?
        return {
            key: value for (key, value) in decode_headers(request_response["headers"])
        }
    else:
        raise Exception("Unable to extract headers from request when logging request.")


@inject
def _log_all_api_requests(
    request: MiddlewareRequestDict,
    response: MiddlewareResponseDict,
    config: Config,
    log: Logger,
):
    request_headers_safe: dict[str, str] = _headers_as_dict(request)

    correlation_id = _get_correlation_id(request, response, log)

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

    server = request.get("server")
    client = request.get("client")
    log.info(
        INCOMING_REQUEST_MESSAGE,
        request["method"],
        request["path"],
        # ASGI spec states `server` and `client`
        # can be `None` if not available.
        f"{server[0]}:{server[1]}" if server else "None",
        f"{client[0]}:{client[1]}" if client else "None",
        request.get("remote_user"),  # FIXME fix this when auth is done
        extra={
            "props": {
                "correlation_id": correlation_id,
                "headers": request_headers_safe,
            }
        },
    )


def _wrap_all_api_responses(
    request: MiddlewareRequestDict,
    response: MiddlewareResponseDict,
    config: Config,
    log: Logger,
):
    correlation_id = _get_correlation_id(request, response, log)
    response_headers = _headers_as_dict(response)

    cors_domain: str | None = None
    if config.web.security.cors.origin:
        cors_domain = config.web.security.cors.origin
    else:
        if not response_headers.get(CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER):
            request_headers = _headers_as_dict(request)
            cors_domain = request_headers.get(ORIGIN_HEADER)
            if not cors_domain:
                cors_domain = request_headers.get(HOST_HEADER)

    if cors_domain:
        response_headers[CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER] = cors_domain

    response_headers[CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER] = str(
        config.web.security.cors.allow_credentials
    )

    response_headers[CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER] = ",".join(
        config.web.security.cors.allow_methods
    )

    response_headers[CORRELATION_ID_HEADER] = correlation_id

    if config.web.security.csp:
        response_headers[CONTENT_SECURITY_POLICY_HEADER] = config.web.security.csp

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


def _log_all_api_responses(
    request: MiddlewareRequestDict,
    response: MiddlewareResponseDict,
    config: Config,
    log: Logger,
):
    response_headers_safe: dict[str, str] = _headers_as_dict(response)

    correlation_id = _get_correlation_id(request, response, log)

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
        response["status"],
        response["status"],
        extra={
            "props": {
                "correlation_id": correlation_id,
                "headers": response_headers_safe,
            }
        },
    )


def decode_headers(headers: list[tuple[bytes, bytes]]):
    content_type = utils.extract_content_type(headers)
    _, encoding = utils.split_content_type(content_type)
    if encoding is None:
        encoding = "utf-8"

    decoded_headers = [
        (header.decode(encoding), value.decode(encoding)) for (header, value) in headers
    ]

    return decoded_headers


def encode_headers(
    headers: list[tuple[bytes, bytes]],
    append_headers: list[tuple[str, str]],
    encoding: str = "utf-8",
):
    for header, value in append_headers:
        headers.append((header.encode(encoding), value.encode(encoding)))


class RequestLoggerMiddleware:
    _app: ASGIApp

    def __init__(self, app: ASGIApp):
        super().__init__()
        self._app = app

    @inject
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send, config: Config, log: Logger
    ) -> None:
        async def wrapped_send(message: Any) -> None:
            nonlocal scope
            nonlocal receive
            nonlocal send

            if message["type"] != "http.response.start":
                return await send(message)

            response = cast(MiddlewareResponseDict, scope)
            request = cast(MiddlewareRequestDict, scope)

            _log_all_api_requests(request, response, config, log)

            return await send(message)

        await self._app(scope, receive, wrapped_send)


class ResponseLoggerMiddleware:
    _app: ASGIApp

    def __init__(self, app: ASGIApp):
        super().__init__()
        self._app = app

    @inject
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send, config: Config, log: Logger
    ) -> None:
        async def wrapped_send(message: Any) -> None:
            nonlocal scope
            nonlocal receive
            nonlocal send

            if message["type"] != "http.response.start":
                return await send(message)

            request = cast(MiddlewareRequestDict, scope)
            response = cast(MiddlewareResponseDict, message)

            _log_all_api_responses(request, response, config, log)
            _wrap_all_api_responses(request, response, config, log)

            return await send(message)

        await self._app(scope, receive, wrapped_send)


class CorrelationIDMiddleware:
    _app: ASGIApp

    def __init__(self, app: ASGIApp):
        super().__init__()
        self._app = app

    @inject
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send, log: Logger
    ) -> None:
        async def wrapped_send(message: Any) -> None:
            nonlocal scope
            nonlocal send

            if message["type"] != "http.response.start":
                return await send(message)

            request = cast(MiddlewareRequestDict, scope)
            response = cast(MiddlewareResponseDict, message)

            response_headers = response["headers"]
            content_type = utils.extract_content_type(response_headers)
            _, encoding = utils.split_content_type(content_type)
            if encoding is None:
                encoding = "utf-8"

            request_headers = request["headers"]
            try:
                correlation_id_header_encoded = CORRELATION_ID_HEADER.lower().encode(
                    encoding
                )

                request_correlation_id: bytes | None = next(
                    (
                        correlation_id
                        for (header, correlation_id) in request_headers
                        if header == correlation_id_header_encoded
                    ),
                    None,
                )

                if request_correlation_id:
                    # validate format
                    _ = uuid.UUID(request_correlation_id.decode(encoding))
                else:
                    request_correlation_id = str(uuid4()).encode(encoding)
                    request_headers.append(
                        (correlation_id_header_encoded, request_correlation_id)
                    )
                    log.info(
                        f'Generated new UUID "{request_correlation_id}" for {CORRELATION_ID_HEADER} request header.'
                    )

                response_headers.append(
                    (correlation_id_header_encoded, request_correlation_id)
                )

                return await send(message)
            except ValueError as e:
                log.warning(
                    f"Badly formatted {CORRELATION_ID_HEADER} received in request."
                )
                raise e

        await self._app(scope, receive, wrapped_send)


def register_openapi_api_request_handlers(app: FlaskApp):
    app.add_middleware(RequestLoggerMiddleware)


def register_openapi_api_response_handlers(app: FlaskApp):
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(ResponseLoggerMiddleware)
