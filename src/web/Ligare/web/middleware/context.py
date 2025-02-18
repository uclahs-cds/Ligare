import uuid
from collections.abc import Collection
from contextvars import ContextVar
from logging import Logger
from typing import Any, Callable, Literal, NamedTuple, NewType, TypedDict, cast
from uuid import uuid4

from connexion import ConnexionMiddleware
from injector import inject
from Ligare.programming.collections.dict import AnyDict
from Ligare.web.middleware.consts import CORRELATION_ID_HEADER
from starlette.types import ASGIApp, Receive, Scope, Send
from typing_extensions import final

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


# copied from connexion.utils
def extract_content_type(
    headers: list[tuple[bytes, bytes]] | dict[str, str],
) -> str | None:
    """Extract the mime type and encoding from the content type headers.

    :param headers: Headers from ASGI scope

    :return: The content type if available in headers, otherwise None
    """
    content_type: str | None = None

    header_pairs: Collection[tuple[str | bytes, str | bytes]] = (
        headers.items() if isinstance(headers, dict) else headers
    )
    for key, value in header_pairs:
        # Headers can always be decoded using latin-1:
        # https://stackoverflow.com/a/27357138/4098821
        if isinstance(key, bytes):
            decoded_key: str = key.decode("latin-1")
        else:
            decoded_key = key

        if decoded_key.lower() == "content-type":
            if isinstance(value, bytes):
                content_type = value.decode("latin-1")
            else:
                content_type = value
            break

    return content_type


# copied from connexion.utils
def split_content_type(content_type: str | None) -> tuple[str | None, str | None]:
    """Split the content type in mime_type and encoding. Other parameters are ignored."""
    mime_type, encoding = None, None

    if content_type is None:
        return mime_type, encoding

    # Check for parameters
    if ";" in content_type:
        mime_type, parameters = content_type.split(";", maxsplit=1)

        # Find parameter describing the charset
        prefix = "charset="
        for parameter in parameters.split(";"):
            if parameter.startswith(prefix):
                encoding = parameter[len(prefix) :]
    else:
        mime_type = content_type
    return mime_type, encoding


RequestId = NewType("RequestId", str)
CorrelationId = NewType("CorrelationId", str)

REQUEST_ID_CTX_KEY = "requestId"
CORRELATION_ID_CTX_KEY = "correlationId"

_request_id_ctx_var: ContextVar[RequestId | None] = ContextVar(
    REQUEST_ID_CTX_KEY, default=None
)
_correlation_id_ctx_var: ContextVar[CorrelationId | None] = ContextVar(
    CORRELATION_ID_CTX_KEY, default=None
)


class TraceId(NamedTuple):
    CorrelationId: CorrelationId | None
    RequestId: RequestId | None


def get_trace_id() -> TraceId:
    return TraceId(_correlation_id_ctx_var.get(), _request_id_ctx_var.get())


@final
class CorrelationIdMiddleware:
    """
    Generate a Correlation ID for each request.

    https://github.com/encode/starlette/issues/420
    """

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        correlation_id = _correlation_id_ctx_var.set(CorrelationId(str(uuid4())))

        await self.app(scope, receive, send)

        _correlation_id_ctx_var.reset(correlation_id)


@final
class RequestIdMiddleware:
    """
    Generate a Trace ID for each request.
    If X-Correlation-Id is set in the request headers, that ID is used instead.
    """

    _app: ASGIApp

    def __init__(self, app: ASGIApp):
        super().__init__()
        self._app = app

    @inject
    async def __call__(
        self, scope: Scope, receive: Receive, send: Send, log: Logger
    ) -> None:
        if scope["type"] not in ["http", "websocket"]:
            return await self._app(scope, receive, send)

        # extract the request ID from the request headers if it is set

        request = cast(MiddlewareRequestDict, scope)
        request_headers = request.get("headers")

        content_type = extract_content_type(request_headers)
        _, encoding = split_content_type(content_type)
        if encoding is None:
            encoding = "utf-8"

        try:
            request_id_header_encoded = CORRELATION_ID_HEADER.lower().encode(encoding)

            request_id: bytes | None = next(
                (
                    request_id
                    for (header, request_id) in request_headers
                    if header == request_id_header_encoded
                ),
                None,
            )

            if request_id:
                # validate format
                request_id_decoded = request_id.decode(encoding)
                _ = uuid.UUID(request_id_decoded)
                request_id_token = _request_id_ctx_var.set(
                    RequestId(request_id_decoded)
                )
            else:
                request_id_decoded = str(uuid4())
                request_id = request_id_decoded.encode(encoding)
                request_headers.append((
                    request_id_header_encoded,
                    request_id,
                ))
                request_id_token = _request_id_ctx_var.set(
                    RequestId(request_id_decoded)
                )
                log.info(
                    f'Generated new UUID "{request_id}" for {CORRELATION_ID_HEADER} request header.'
                )
        except ValueError as e:
            log.warning(f"Badly formatted {CORRELATION_ID_HEADER} received in request.")
            raise e

        async def wrapped_send(message: Any) -> None:
            nonlocal scope
            nonlocal send

            if message["type"] != "http.response.start":
                return await send(message)

            # include the request ID in response headers

            response = cast(MiddlewareResponseDict, message)
            response_headers = response["headers"]

            content_type = extract_content_type(response_headers)
            _, encoding = split_content_type(content_type)
            if encoding is None:
                encoding = "utf-8"

            response_headers.append((
                request_id_header_encoded,
                request_id,
            ))

            return await send(message)

        await self._app(scope, receive, wrapped_send)

        _request_id_ctx_var.reset(request_id_token)
