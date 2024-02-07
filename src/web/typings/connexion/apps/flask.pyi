"""
This type stub file was generated by pyright.
"""

import pathlib
import typing as t

from connexion import ConnexionMiddleware
from connexion.apps.abstract import AbstractApp
from connexion.jsonifier import Jsonifier
from connexion.lifecycle import ConnexionRequest, ConnexionResponse
from connexion.middleware.abstract import AbstractRoutingAPI, SpecMiddleware
from connexion.middleware.lifespan import Lifespan
from connexion.operations import AbstractOperation
from connexion.options import SwaggerUIOptions
from connexion.resolver import Resolver
from connexion.types import MaybeAwaitable, WSGIApp
from connexion.uri_parsing import AbstractURIParser
from flask import Flask
from flask import Response as FlaskResponse
from starlette.types import Receive, Scope, Send
from typing_extensions import override

"""
This module defines a FlaskApp, a Connexion application to wrap a Flask application.
"""

class FlaskOperation:
    def __init__(
        self,
        fn: t.Callable[..., t.Any],
        jsonifier: Jsonifier,
        operation_id: str,
        pythonic_params: bool,
    ) -> None: ...
    @classmethod
    def from_operation(
        cls,
        operation: AbstractOperation,
        *,
        pythonic_params: bool,
        jsonifier: Jsonifier,
    ) -> FlaskOperation: ...
    @property
    def fn(self) -> t.Callable[..., t.Any]: ...
    def __call__(self, *args: list[t.Any], **kwargs: t.Any) -> FlaskResponse: ...
    _fn: t.Callable[..., t.Any]

class FlaskApi(AbstractRoutingAPI[t.Any]):
    def __init__(
        self,
        *args: list[t.Any],
        jsonifier: t.Optional[Jsonifier] = ...,
        **kwargs: t.Any,
    ) -> None: ...
    @override
    def make_operation(self, operation: t.Any) -> FlaskOperation: ...
    def add_url_rule(
        self,
        rule: t.Any,
        endpoint: str = ...,
        view_func: t.Callable[..., t.Any] = ...,
        **options: t.Any,
    ) -> None: ...

class FlaskASGIApp(SpecMiddleware):
    def __init__(
        self, import_name: str, server_args: dict[t.Any, t.Any], **kwargs: t.Any
    ) -> None: ...
    @override
    def add_api(
        self, specification: t.Any, *, name: str = ..., **kwargs: t.Any
    ) -> FlaskApi: ...
    def add_url_rule(
        self,
        rule: t.Any,
        endpoint: str = ...,
        view_func: t.Callable[..., t.Any] = ...,
        **options: t.Any,
    ) -> None: ...
    @override
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None: ...

    app: Flask

class FlaskApp(AbstractApp):
    """Connexion Application based on ConnexionMiddleware wrapping a Flask application."""

    app: Flask
    _middleware_app: FlaskASGIApp  # pyright: ignore[reportIncompatibleVariableOverride]
    middleware: ConnexionMiddleware | None = ...
    def __init__(
        self,
        import_name: str,
        *,
        lifespan: t.Optional[Lifespan] = ...,
        middlewares: t.Optional[list[t.Any]] = ...,
        server_args: t.Optional[dict[t.Any, t.Any]] = ...,
        specification_dir: t.Union[pathlib.Path, str] = ...,
        arguments: t.Optional[dict[t.Any, t.Any]] = ...,
        auth_all_paths: t.Optional[bool] = ...,
        jsonifier: t.Optional[Jsonifier] = ...,
        pythonic_params: t.Optional[bool] = ...,
        resolver: t.Optional[t.Union[Resolver, t.Callable[..., t.Any]]] = ...,
        resolver_error: t.Optional[int] = ...,
        strict_validation: t.Optional[bool] = ...,
        swagger_ui_options: t.Optional[SwaggerUIOptions] = ...,
        uri_parser_class: t.Optional[AbstractURIParser] = ...,
        validate_responses: t.Optional[bool] = ...,
        validator_map: t.Optional[dict[t.Any, t.Any]] = ...,
        security_map: t.Optional[dict[t.Any, t.Any]] = ...,
    ) -> None:
        """
        :param import_name: The name of the package or module that this object belongs to. If you
            are using a single module, __name__ is always the correct value. If you however are
            using a package, it’s usually recommended to hardcode the name of your package there.
        :param lifespan: A lifespan context function, which can be used to perform startup and
            shutdown tasks.
        :param middlewares: The list of middlewares to wrap around the application. Defaults to
            :obj:`middleware.main.ConnexionMiddleware.default_middlewares`
        :param server_args: Arguments to pass to the Flask application.
        :param specification_dir: The directory holding the specification(s). The provided path
            should either be absolute or relative to the root path of the application. Defaults to
            the root path.
        :param arguments: Arguments to substitute the specification using Jinja.
        :param auth_all_paths: whether to authenticate not paths not defined in the specification.
            Defaults to False.
        :param jsonifier: Custom jsonifier to overwrite json encoding for json responses.
        :param swagger_ui_options: A :class:`options.ConnexionOptions` instance with configuration
            options for the swagger ui.
        :param pythonic_params: When True, CamelCase parameters are converted to snake_case and an
            underscore is appended to any shadowed built-ins. Defaults to False.
        :param resolver: Callable that maps operationId to a function or instance of
            :class:`resolver.Resolver`.
        :param resolver_error: Error code to return for operations for which the operationId could
            not be resolved. If no error code is provided, the application will fail when trying to
            start.
        :param strict_validation: When True, extra form or query parameters not defined in the
            specification result in a validation error. Defaults to False.
        :param swagger_ui_options: Instance of :class:`options.ConnexionOptions` with
            configuration options for the swagger ui.
        :param uri_parser_class: Class to use for uri parsing. See :mod:`uri_parsing`.
        :param validate_responses: Whether to validate responses against the specification. This has
            an impact on performance. Defaults to False.
        :param validator_map: A dictionary of validators to use. Defaults to
            :obj:`validators.VALIDATOR_MAP`.
        :param security_map: A dictionary of security handlers to use. Defaults to
            :obj:`security.SECURITY_HANDLERS`
        """
        ...
    @override
    def add_url_rule(
        self,
        rule: str,
        endpoint: str = ...,
        view_func: t.Callable[..., t.Any] = ...,
        **options: t.Any,
    ) -> None: ...
    @override
    def add_error_handler(
        self,
        code_or_exception: t.Union[int, t.Type[Exception]],
        function: t.Callable[
            [ConnexionRequest, Exception], MaybeAwaitable[ConnexionResponse]
        ],
    ) -> None: ...
    def add_wsgi_middleware(
        self, middleware: t.Type[WSGIApp], **options: t.Any
    ) -> None:
        """Wrap the underlying Flask application with a WSGI middleware. Note that it will only be
        called at the end of the middleware stack. Middleware that needs to act sooner, needs to
        be added as ASGI middleware instead.

        Adding multiple middleware using this method wraps each middleware around the previous one.

        :param middleware: Middleware class to add
        :param options: Options to pass to the middleware_class on initialization
        """
        ...
