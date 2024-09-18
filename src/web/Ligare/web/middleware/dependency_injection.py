from functools import partial
from typing import Any, Callable, Protocol, Tuple, Type, cast

from connexion import ConnexionMiddleware, FlaskApp
from connexion.apps.flask import FlaskASGIApp, FlaskOperation
from connexion.middleware.main import MiddlewarePosition
from flask import Config as Config
from flask import Flask
from flask_injector import FlaskInjector, wrap_function
from injector import Binder, Injector, Module
from Ligare.programming.patterns.dependency_injection import LoggerModule
from starlette.types import ASGIApp, Receive, Scope, Send
from typing_extensions import override

from . import RegisterMiddlewareCallback, TFlaskApp


class MiddlewareRoutine(Protocol):
    def __call__(
        self, scope: Scope, receive: Receive, send: Send, *args: Any
    ) -> None: ...


class AppModule(Module):
    def __init__(self, app: TFlaskApp, *args: Tuple[Any, Any]) -> None:
        super().__init__()
        if isinstance(app, Flask):
            self._flask_app = app
        elif isinstance(app, FlaskApp):  # pyright: ignore[reportUnnecessaryIsInstance] guard against things like not using `MagicMock(spec=...)`
            self._flask_app = app.app
        else:
            raise ValueError(
                f"Wrong type provided for Flask instance. Provided type is `{type(app)}` but excepted `{TFlaskApp}`."
            )

        self._other_dependencies = args

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(Flask, to=self._flask_app)
        binder.bind(Config, to=self._flask_app.config)
        binder.install(LoggerModule(self._flask_app.name))

        for dependency in self._other_dependencies:
            binder.bind(dependency[0], to=dependency[1])


def configure_dependencies(
    app: TFlaskApp,
    application_modules: list[Module | type[Module]] | None = None,
) -> FlaskInjector:
    """
    Configures dependency injection and registers all Flask
    application dependencies. The FlaskInjector instance
    can be used to bootstrap and start the Flask application.
    """
    if isinstance(app, FlaskApp):
        flask_app = app.app
    else:
        flask_app = app

    modules = [
        (module if isinstance(module, Module) else module())
        for module in [AppModule(app)]
        + (application_modules if application_modules else [])
    ]

    # bootstrap the flask application and its dependencies
    flask_injector = FlaskInjector(flask_app, modules)

    flask_injector.injector.binder.bind(Injector, flask_injector.injector)

    if isinstance(app, FlaskApp):
        app.add_middleware(OpenAPIEndpointDependencyInjectionMiddleware(flask_injector))

        # For every module registered, check if any are "middleware" type modules.
        # if they are, they need to be registered with the application.
        # In the event the application is a Connexion application,
        # this needs to happen after _configure_openapi_middleware_dependencies
        # because the middleware is a "FILO" stack - the items are the end
        # of the stack are executed first. By ensuring this happens before
        # OpenAPIEndpointDependencyInjectionMiddleware, other Middlewares
        # can alter routing information.
        # TODO this needs to happen in some form for plain Flask applications too.
        for module in modules:
            register_callback: RegisterMiddlewareCallback | None = getattr(
                module, "register_middleware", None
            )
            if register_callback is not None and callable(register_callback):
                flask_injector.injector.call_with_injection(
                    register_callback, kwargs={"app": app}
                )

        # this binds all Ligare middlewares with Injector
        _configure_openapi_middleware_dependencies(app, flask_injector)

    return flask_injector


class OpenAPIEndpointDependencyInjectionMiddleware:
    """
    Enables dependency injection for any blueprint methods.
    """

    def __new__(cls, flask_injector: FlaskInjector):
        class _InternalDependencyInjectionMiddleware:
            """
            This is a means of applying partial application over a class, rather than a function.
            It is done this way to jive with Connexion/Starlette's middleware system.
            The inclusion of a flask_injector parameters lets us use that instance
            when setting up the middleware without violating the contract that Starlette expects.
            """

            def __init__(
                self,
                app: ASGIApp,
                flask_injector: FlaskInjector | None = flask_injector,
            ) -> None:
                super().__init__()
                self._app = app
                self._flask_injector = flask_injector

            async def __call__(
                self, scope: Scope, receive: Receive, send: Send
            ) -> None:
                async def wrapped_send(message: Any) -> None:
                    nonlocal scope
                    nonlocal receive
                    nonlocal send

                    # Only run during startup of the application
                    if (
                        (
                            scope["type"] != "lifespan"
                            and message["type"] != "lifespan.startup.complete"
                        )
                        or not scope["app"]
                        or self._flask_injector == None
                    ):
                        return await send(message)

                    # Find every registered route
                    connexion_app = cast(ConnexionMiddleware, scope["app"])

                    if not connexion_app.middleware_stack:
                        return await send(message)

                    flask_asgi_app = next(
                        (
                            middleware
                            for middleware in scope["app"].middleware_stack
                            if isinstance(middleware, FlaskASGIApp)
                        ),
                        None,
                    )

                    if not flask_asgi_app:
                        return await send(message)

                    endpoints = cast(
                        dict[str, FlaskOperation | Callable[..., Any]],
                        flask_asgi_app.app.view_functions,
                    )

                    for endpoint_name, endpoint in endpoints.items():
                        # Skip anything that does not have `@inject` applied
                        if not hasattr(endpoint, "__bindings__"):
                            continue

                        if hasattr(endpoint, "_fn") and isinstance(
                            endpoint, FlaskOperation
                        ):
                            # _fn is the original function that ends up being called.
                            # we wrap it with Injector, then replace it
                            endpoints[endpoint_name]._fn = wrap_function(  # pyright: ignore[reportFunctionMemberAccess]
                                endpoint._fn,
                                self._flask_injector.injector,
                            )
                        # If a blueprint is added through anything other than
                        # by Connexion, `_fn` is not set. This happens with, e.g.,
                        # the SSO blueprint.
                        else:
                            if callable(endpoint):
                                endpoints[endpoint_name] = wrap_function(
                                    endpoint,
                                    self._flask_injector.injector,
                                )

                    return await send(message)

                await self._app(scope, receive, wrapped_send)

        return type(
            "_DependencyInjectionMiddleware",
            (_InternalDependencyInjectionMiddleware,),
            {},
        )


def bind_middleware(
    app: TFlaskApp,
    flask_injector: FlaskInjector,
    middleware: Type[ASGIApp],
    position: MiddlewarePosition = MiddlewarePosition.BEFORE_CONTEXT,
):
    middleware_class: Callable[..., Any] = middleware

    # hasn't been registered with the application yet
    if not isinstance(middleware, partial):
        if not isinstance(app, FlaskApp):
            return

        app.add_middleware(middleware_class, position)
    else:
        middleware_class = middleware.func

    # Connexion/Starlette middleware are classes w/ a __call__ method
    middleware_routine = cast(
        MiddlewareRoutine | None, getattr(middleware_class, "__call__", None)
    )
    if not middleware_routine:
        return

    # Skip any __call__ methods without `@inject` applied
    if not hasattr(middleware_routine, "__bindings__"):
        return

    # Wrap the __call__ method and replace the original with the now-wrapped method
    middleware_class.__call__ = (  # pyright: ignore[reportFunctionMemberAccess]
        wrap_function(middleware_routine, flask_injector.injector)
    )


def _configure_openapi_middleware_dependencies(
    app: TFlaskApp, flask_injector: FlaskInjector
):
    """
    Bind any Connexion middleware classes whose __call__ member has a __bindings__ attribute.
    This attribute signals that @inject was used on it.
    """

    app_middleware = getattr(app, "middleware", None)
    if not app_middleware:
        return

    app_middlewares = getattr(app_middleware, "middlewares", None)
    if not app_middlewares:
        return

    for middleware in cast(list[type], app_middlewares):
        # these are all middlewares that are registered by Connexion
        # so we can skip them
        if not isinstance(middleware, partial):
            continue

        bind_middleware(app, flask_injector, middleware)
