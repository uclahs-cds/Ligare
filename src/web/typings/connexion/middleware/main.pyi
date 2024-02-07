"""
This type stub file was generated by pyright.
"""

import enum
import pathlib
import typing as t
from dataclasses import dataclass

from connexion.jsonifier import Jsonifier
from connexion.lifecycle import ConnexionRequest, ConnexionResponse
from connexion.middleware.lifespan import Lifespan
from connexion.options import SwaggerUIOptions
from connexion.resolver import Resolver
from connexion.types import MaybeAwaitable
from connexion.uri_parsing import AbstractURIParser
from starlette.types import ASGIApp, Receive, Scope, Send

logger = ...

@dataclass
class _Options:
    """
    Connexion provides a lot of parameters for the user to configure the app / middleware of
    application.

    This class provides a central place to parse these parameters a mechanism to update them.
    Application level arguments can be provided when instantiating the application / middleware,
    after which they can be overwritten on an API level.

    The defaults should only be set in this class, and set to None in the signature of user facing
    methods. This is necessary for this class to be able to differentiate between missing and
    falsy arguments.
    """

    arguments: t.Optional[dict] = ...
    auth_all_paths: t.Optional[bool] = ...
    jsonifier: t.Optional[Jsonifier] = ...
    pythonic_params: t.Optional[bool] = ...
    resolver: t.Optional[t.Union[Resolver, t.Callable]] = ...
    resolver_error: t.Optional[int] = ...
    resolver_error_handler: t.Optional[t.Callable] = ...
    strict_validation: t.Optional[bool] = ...
    swagger_ui_options: t.Optional[SwaggerUIOptions] = ...
    uri_parser_class: t.Optional[AbstractURIParser] = ...
    validate_responses: t.Optional[bool] = ...
    validator_map: t.Optional[dict] = ...
    security_map: t.Optional[dict] = ...
    def __post_init__(self):  # -> None:
        ...
    def replace(self, **changes) -> _Options:
        """Update mechanism to overwrite the options. None values are discarded.

        :param changes: Arguments accepted by the __init__ method of this class.

        :return: An new _Options object with updated arguments.
        """
        ...

class MiddlewarePosition(enum.Enum):
    """Positions to insert a middleware"""

    BEFORE_EXCEPTION = ...
    BEFORE_SWAGGER = ...
    BEFORE_ROUTING = ...
    BEFORE_SECURITY = ...
    BEFORE_VALIDATION = ...
    BEFORE_CONTEXT = ...

class API:
    def __init__(self, specification, *, base_path, **kwargs) -> None: ...

class ConnexionMiddleware:
    """The main Connexion middleware, which wraps a list of specialized middlewares around the
    provided application."""

    default_middlewares = ...
    middlewares: list[type] | None = ...
    def __init__(
        self,
        app: ASGIApp,
        *,
        import_name: t.Optional[str] = ...,
        lifespan: t.Optional[Lifespan] = ...,
        middlewares: t.Optional[t.List[ASGIApp]] = ...,
        specification_dir: t.Union[pathlib.Path, str] = ...,
        arguments: t.Optional[dict] = ...,
        auth_all_paths: t.Optional[bool] = ...,
        jsonifier: t.Optional[Jsonifier] = ...,
        pythonic_params: t.Optional[bool] = ...,
        resolver: t.Optional[t.Union[Resolver, t.Callable]] = ...,
        resolver_error: t.Optional[int] = ...,
        strict_validation: t.Optional[bool] = ...,
        swagger_ui_options: t.Optional[SwaggerUIOptions] = ...,
        uri_parser_class: t.Optional[AbstractURIParser] = ...,
        validate_responses: t.Optional[bool] = ...,
        validator_map: t.Optional[dict] = ...,
        security_map: t.Optional[dict] = ...,
    ) -> None:
        """
        :param import_name: The name of the package or module that this object belongs to. If you
            are using a single module, __name__ is always the correct value. If you however are
            using a package, it’s usually recommended to hardcode the name of your package there.
        :param middlewares: The list of middlewares to wrap around the application. Defaults to
            :obj:`middleware.main.ConnexionmMiddleware.default_middlewares`
        :param specification_dir: The directory holding the specification(s). The provided path
            should either be absolute or relative to the root path of the application. Defaults to
            the root path.
        :param arguments: Arguments to substitute the specification using Jinja.
        :param auth_all_paths: whether to authenticate not paths not defined in the specification.
            Defaults to False.
        :param jsonifier: Custom jsonifier to overwrite json encoding for json responses.
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
            :obj:`security.SECURITY_HANDLERS`.
        """
        ...
    def add_middleware(
        self,
        middleware_class: t.Type[ASGIApp] | t.Any,
        *,
        position: MiddlewarePosition = ...,
        **options: t.Any,
    ) -> None:
        """Add a middleware to the stack on the specified position.

        :param middleware_class: Middleware class to add
        :param position: Position to add the middleware, one of the MiddlewarePosition Enum
        :param options: Options to pass to the middleware_class on initialization
        """
        ...
    def add_api(
        self,
        specification: t.Union[pathlib.Path, str, dict],
        *,
        base_path: t.Optional[str] = ...,
        name: t.Optional[str] = ...,
        arguments: t.Optional[dict] = ...,
        auth_all_paths: t.Optional[bool] = ...,
        jsonifier: t.Optional[Jsonifier] = ...,
        pythonic_params: t.Optional[bool] = ...,
        resolver: t.Optional[t.Union[Resolver, t.Callable]] = ...,
        resolver_error: t.Optional[int] = ...,
        strict_validation: t.Optional[bool] = ...,
        swagger_ui_options: t.Optional[SwaggerUIOptions] = ...,
        uri_parser_class: t.Optional[AbstractURIParser] = ...,
        validate_responses: t.Optional[bool] = ...,
        validator_map: t.Optional[dict] = ...,
        security_map: t.Optional[dict] = ...,
        **kwargs,
    ) -> None:
        """
        Register een API represented by a single OpenAPI specification on this middleware.
        Multiple APIs can be registered on a single middleware.

        :param specification: OpenAPI specification. Can be provided either as dict, or as path
            to file.
        :param base_path: Base path to host the API. This overrides the basePath / servers in the
            specification.
        :param name: Name to register the API with. If no name is passed, the base_path is used
            as name instead.
        :param arguments: Arguments to substitute the specification using Jinja.
        :param auth_all_paths: whether to authenticate not paths not defined in the specification.
            Defaults to False.
        :param jsonifier: Custom jsonifier to overwrite json encoding for json responses.
        :param pythonic_params: When True, CamelCase parameters are converted to snake_case and an
            underscore is appended to any shadowed built-ins. Defaults to False.
        :param resolver: Callable that maps operationId to a function or instance of
            :class:`resolver.Resolver`.
        :param resolver_error: Error code to return for operations for which the operationId could
            not be resolved. If no error code is provided, the application will fail when trying to
            start.
        :param strict_validation: When True, extra form or query parameters not defined in the
            specification result in a validation error. Defaults to False.
        :param swagger_ui_options: A dict with configuration options for the swagger ui. See
            :class:`options.ConnexionOptions`.
        :param uri_parser_class: Class to use for uri parsing. See :mod:`uri_parsing`.
        :param validate_responses: Whether to validate responses against the specification. This has
            an impact on performance. Defaults to False.
        :param validator_map: A dictionary of validators to use. Defaults to
            :obj:`validators.VALIDATOR_MAP`
        :param security_map: A dictionary of security handlers to use. Defaults to
            :obj:`security.SECURITY_HANDLERS`
        :param kwargs: Additional keyword arguments to pass to the `add_api` method of the managed
            middlewares. This can be used to pass arguments to middlewares added beyond the default
            ones.

        :return: The Api registered on the wrapped application.
        """
        ...
    def add_error_handler(
        self,
        code_or_exception: t.Union[int, t.Type[Exception]],
        function: t.Callable[
            [ConnexionRequest, Exception], MaybeAwaitable[ConnexionResponse]
        ],
    ) -> None:
        """
        Register a callable to handle application errors.

        :param code_or_exception: An exception class or the status code of HTTP exceptions to
            handle.
        :param function: Callable that will handle exception, may be async.
        """
        ...
    def run(self, import_string: str = ..., **kwargs):  # -> None:
        """Run the application using uvicorn.

        :param import_string: application as import string (eg. "main:app"). This is needed to run
                              using reload.
        :param kwargs: kwargs to pass to `uvicorn.run`.
        """
        ...
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None: ...
    middleware_stack: t.Optional[t.Iterable[ASGIApp]] = None
