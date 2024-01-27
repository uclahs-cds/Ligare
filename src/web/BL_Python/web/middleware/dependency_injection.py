from functools import partial
from typing import Any, Callable, Protocol, Tuple, cast

from BL_Python.programming.patterns.dependency_injection import LoggerModule
from connexion import FlaskApp
from flask import Config as Config
from flask import Flask
from flask_injector import FlaskInjector, wrap_function
from injector import Binder, Injector, Module
from starlette.types import Receive, Scope, Send
from typing_extensions import override

from . import TFlaskApp


class AppModule(Module):
    def __init__(self, app: TFlaskApp, *args: Tuple[Any, Any]) -> None:
        super().__init__()
        if isinstance(app, Flask):
            self._flask_app = app
        elif isinstance(
            app, FlaskApp
        ):  # pyright: ignore[reportUnnecessaryIsInstance] guard against things like not using `MagicMock(spec=...)`
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


# class AppModule(Module):
#    def __init__(self, app: TFlaskApp, *args: Tuple[Any, Any]) -> None:
#        super().__init__()
#        if isinstance(app, Flask):
#            self._flask_app = app
#        else:
#            self._flask_app = app.app
#        self._other_dependencies = args
#
#    @override
#    def configure(self, binder: Binder) -> None:
#        binder.bind(Flask, to=self._flask_app)
#        binder.bind(Config, to=self._flask_app.config)
#        binder.install(LoggerModule(self._flask_app.name))
#
#        for dependency in self._other_dependencies:
#            binder.bind(dependency[0], to=dependency[1])


class MiddlewareRoutine(Protocol):
    def __call__(self, scope: Scope, receive: Receive, send: Send, *args: Any) -> None:
        ...


def configure_dependencies(
    app: TFlaskApp,
    application_modules: list[Module] | None = None,
) -> FlaskInjector:
    """
    Configures dependency injection and registers all Flask
    application dependencies. The FlaskInjector instance
    can be used to bootstrap and start the Flask application.
    """
    if isinstance(app, FlaskApp):
        flask_app = app.app  # .app
    else:
        flask_app = app

    modules = [AppModule(app)] + (application_modules if application_modules else [])

    # bootstrap the flask application and its dependencies
    flask_injector = FlaskInjector(flask_app, modules)

    flask_injector.injector.binder.bind(Injector, flask_injector.injector)

    return _configure_connexion_dependencies(app, flask_injector)


def _configure_connexion_dependencies(
    app: TFlaskApp, flask_injector: FlaskInjector
) -> FlaskInjector:
    """
    Bind any Connexion middleware classes whose __call__ member has a __bindings__ attribute.
    This attribute signals that @inject was used on it.
    """
    if not isinstance(app, FlaskApp):
        return flask_injector

    app_middleware = getattr(app, "middleware", None)
    if not app_middleware:
        return flask_injector

    app_middlewares = getattr(app_middleware, "middlewares", None)
    if not app_middlewares:
        return flask_injector

    for middleware in cast(list[type], app_middlewares):
        if not isinstance(middleware, partial):
            continue
        middleware_class = middleware.func
        middleware_routine = cast(
            MiddlewareRoutine | None, getattr(middleware_class, "__call__", None)
        )
        if not middleware_routine:
            continue

        if not hasattr(middleware_routine, "__bindings__"):
            continue

        middleware_class.__call__ = (  # pyright: ignore[reportFunctionMemberAccess]
            wrap_function(middleware_routine, flask_injector.injector)
        )

    return flask_injector
