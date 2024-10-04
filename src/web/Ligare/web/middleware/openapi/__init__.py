import re
import uuid
from collections.abc import Iterable
from contextlib import ExitStack
from contextvars import Token
from logging import Logger
from typing import Any, Awaitable, Callable, Literal, TypeAlias, TypeVar, cast
from uuid import uuid4

import json_logging
import starlette
import starlette.datastructures
import starlette.requests
from connexion import ConnexionMiddleware, FlaskApp, context, utils
from connexion.middleware import MiddlewarePosition
from flask import Flask, Request, Response, request
from flask.ctx import AppContext
from flask.globals import _cv_app  # pyright: ignore[reportPrivateUsage]
from flask.globals import current_app
from flask.typing import ResponseReturnValue
from flask_login import AnonymousUserMixin, current_user
from injector import inject
from Ligare.programming.collections.dict import AnyDict, merge
from starlette.datastructures import Address
from starlette.types import ASGIApp, Receive, Scope, Send
from typing_extensions import TypedDict, final
from werkzeug.local import LocalProxy

from ...config import Config
from ..consts import (
    CONTENT_SECURITY_POLICY_HEADER,
    CORRELATION_ID_HEADER,
    INCOMING_REQUEST_MESSAGE,
    OUTGOING_RESPONSE_MESSAGE,
    REQUEST_COOKIE_HEADER,
    RESPONSE_COOKIE_HEADER,
)

# pyright: reportUnusedFunction=false


# Fixes type problems when using @inject with @app.before_request and @app.after_request.
# The main difference with these types as opposed to the Flask-defined types is that
# these types allow the handler to take any arguments, versus no arguments or just Response.
AfterRequestCallable: TypeAlias = (
    Callable[..., Response] | Callable[..., Awaitable[Response]]
)
BeforeRequestCallable: TypeAlias = (
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
        isinstance(request_response, dict)  # pyright: ignore[reportUnnecessaryIsInstance]
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
    app: Flask,
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

    server = get_server_address()
    client = get_remote_address()
    log.info(
        INCOMING_REQUEST_MESSAGE,
        request["method"],
        request["path"],
        # ASGI spec states `server` and `client`
        # can be `None` if not available.
        f"{server.host}:{server.port}",
        f"{client.host}:{client.port}",
        "Anonymous"
        if (
            isinstance(current_user, AnonymousUserMixin)
            or not hasattr(app, "login_manager")
        )
        else current_user.get_id(),
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
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        config: Config,
        log: Logger,
        app: Flask,
    ) -> None:
        async def wrapped_send(message: Any) -> None:
            nonlocal scope
            nonlocal receive
            nonlocal send

            if message["type"] != "http.response.start":
                return await send(message)

            response = cast(MiddlewareResponseDict, scope)
            request = cast(MiddlewareRequestDict, scope)

            _log_all_api_requests(request, response, app, config, log)

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
                    request_headers.append((
                        correlation_id_header_encoded,
                        request_correlation_id,
                    ))
                    log.info(
                        f'Generated new UUID "{request_correlation_id}" for {CORRELATION_ID_HEADER} request header.'
                    )

                response_headers.append((
                    correlation_id_header_encoded,
                    request_correlation_id,
                ))

                return await send(message)
            except ValueError as e:
                log.warning(
                    f"Badly formatted {CORRELATION_ID_HEADER} received in request."
                )
                raise e

        await self._app(scope, receive, wrapped_send)


_DEFAULT_HOSTNAME = "localhost"
_DEFAULT_PORT = 80


def get_server_address() -> Address:
    request_proxy = cast(LocalProxy[starlette.requests.Request], context.request)
    starlette_request = cast(
        starlette.requests.Request, request_proxy._starlette_request
    )
    scope = starlette_request.scope
    server_hostname = starlette_request.base_url.hostname
    server_port = starlette_request.base_url.port
    if not server_hostname or not server_port:
        # there is the possibility this value in scope is "127.0.0.1" when using "localhost"
        # which is not consistent with the _starlette_request value.
        server = cast(tuple[str, int] | None, scope.get("server"))
        if server:
            if not server_hostname:
                server_hostname = server[0]
            if not server_port:
                server_port = server[1]
        else:
            app_server_name = cast(dict[str, str | None], current_app.config).get(
                "SERVER_NAME"
            )
            if app_server_name:
                if not server_hostname:
                    server_hostname = app_server_name[: app_server_name.index(":")]
                if not server_port:
                    server_port = app_server_name[app_server_name.index(":") + 1 :]
    if isinstance(server_port, str):
        try:
            server_port = int(server_port)
        except:
            # this is the same default port that
            # Starlette uses in starlette.middleware.wsgi.build_environ
            server_port = _DEFAULT_PORT

    return Address(
        host=server_hostname or _DEFAULT_HOSTNAME, port=server_port or _DEFAULT_PORT
    )


def get_remote_address() -> Address:
    request_proxy = cast(LocalProxy[starlette.requests.Request], context.request)
    starlette_request = cast(
        starlette.requests.Request, request_proxy._starlette_request
    )
    scope = starlette_request.scope
    request_client = starlette_request.client

    remote_hostname = ""
    remote_port = 0

    if request_client:
        remote_hostname = request_client.host
        remote_port = request_client.port

    if not remote_hostname or not remote_port:
        # it's actually a 2-item list whose first item
        # is a string, and second item is an int ...
        client = cast(tuple[str, int] | None, scope.get("client"))
        if client and isinstance(client, Iterable):  # pyright: ignore[reportUnnecessaryIsInstance]
            if not remote_hostname:
                remote_hostname = client[0]

            if not remote_port:
                remote_port = client[1]

    return Address(host=remote_hostname, port=remote_port)


def address_to_str(address: Address):
    return f"{address.host}:{address.port}"


@final
class FlaskContextMiddleware:
    """
    Connexion does not set Flask contexts in all cases they may be needed, like
    in middlewares that execute before ContextMiddleware. This middleware creates
    the Flask application, request, and session contexts if they are not currently set.
    """

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    @inject
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send, app: Flask
    ) -> None:
        receive_token: Token[Receive] | None = None
        scope_token: Token[Scope] | None = None
        app_ctx_token: Token[AppContext] | None = None

        try:
            receive_token = context._receive.set(receive)  # pyright: ignore[reportPrivateUsage]
            scope_token = context._scope.set(scope)  # pyright: ignore[reportPrivateUsage]

            if scope["type"] not in ["http", "websocket"]:
                await self.app(scope, receive, send)
                return

            with ExitStack() as exit_stack:
                if not isinstance(current_app, Flask):  # pyright: ignore[reportUnnecessaryIsInstance] it is not a Flask if it is not set
                    app_ctx = exit_stack.enter_context(app.app_context())

                    app_ctx_token = _cv_app.set(app_ctx)

                if not isinstance(request, Request):  # pyright: ignore[reportUnnecessaryIsInstance] it is not a Request if it is not set
                    request_proxy = cast(
                        LocalProxy[starlette.requests.Request], context.request
                    )
                    starlette_request = cast(
                        starlette.requests.Request, request_proxy._starlette_request
                    )
                    request_headers = cast(
                        starlette.datastructures.Headers, request_proxy.headers
                    )
                    path_info = (
                        "PATH_INFO",
                        str(scope.get("path") or starlette_request.url.path),
                    )
                    wsgi_url_scheme = (
                        "wsgi.url_scheme",
                        str(scope.get("scheme") or starlette_request.url.scheme),
                    )
                    request_method = (
                        "REQUEST_METHOD",
                        str(scope.get("method") or starlette_request.method),
                    )
                    (server_hostname, server_port) = get_server_address()
                    server_name = ("SERVER_NAME", server_hostname)
                    server_port = ("SERVER_PORT", server_port)
                    query_string = (
                        "QUERY_STRING",
                        scope.get("query_string") or starlette_request.url.query,
                    )
                    remote_addr = ("REMOTE_ADDR", address_to_str(get_remote_address()))
                    headers = dict({
                        (
                            f"{'HTTP_' if header.upper() not in ['CONTENT_TYPE', 'CONTENT_LENGTH'] else ''}{header.upper().replace('-', '_')}",
                            value,
                        )
                        for header, value in request_headers.items()
                    })

                    request_environ = merge(
                        dict([
                            path_info,
                            wsgi_url_scheme,
                            request_method,
                            server_name,
                            server_port,
                            query_string,
                            remote_addr,
                        ]),
                        headers,
                        True,
                    )

                    # Some values, like the query string, are stored as bytes.
                    # Decode as a UTF-8 str so encoding later doesn't fail.
                    for key, value in request_environ.items():
                        if isinstance(value, bytes):
                            request_environ[key] = value.decode("utf-8")

                    request_ctx = exit_stack.enter_context(
                        app.request_context(request_environ)
                    )
                    request_ctx.push()

                await self.app(scope, receive, send)

        finally:
            if app_ctx_token is not None:
                _cv_app.reset(app_ctx_token)
            if receive_token is not None:
                context._receive.reset(receive_token)  # pyright: ignore[reportPrivateUsage]
            if scope_token is not None:
                context._scope.reset(scope_token)  # pyright: ignore[reportPrivateUsage]


def register_openapi_api_request_handlers(app: FlaskApp):
    app.add_middleware(RequestLoggerMiddleware)


def register_openapi_api_response_handlers(app: FlaskApp):
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(ResponseLoggerMiddleware)


def register_openapi_context_middleware(app: FlaskApp):
    app.add_middleware(FlaskContextMiddleware, MiddlewarePosition.BEFORE_EXCEPTION)
