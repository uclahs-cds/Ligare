from dataclasses import dataclass
from functools import wraps
from logging import Logger
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    ParamSpec,
    Sequence,
    TypedDict,
    TypeVar,
    cast,
)

from connexion import FlaskApp, request
from flask import Blueprint, Flask, abort
from injector import Binder, Injector, Module, inject, provider, singleton
from Ligare.database.dependency_injection import ScopedSessionModule
from Ligare.database.types import MetaBase
from Ligare.platform.feature_flag.caching_feature_flag_router import (
    CachingFeatureFlagRouter,
)
from Ligare.platform.feature_flag.caching_feature_flag_router import (
    FeatureFlag as CachingFeatureFlag,
)
from Ligare.platform.feature_flag.db_feature_flag_router import DBFeatureFlagRouter
from Ligare.platform.feature_flag.db_feature_flag_router import (
    FeatureFlag as DBFeatureFlag,
)
from Ligare.platform.feature_flag.db_feature_flag_router import FeatureFlagTableBase
from Ligare.platform.feature_flag.feature_flag_router import (
    FeatureFlag,
    FeatureFlagRouter,
    TFeatureFlag,
)
from Ligare.programming.config import AbstractConfig
from Ligare.programming.patterns.dependency_injection import ConfigurableModule
from Ligare.web.middleware.sso import login_required
from pydantic import BaseModel
from starlette.types import ASGIApp, Receive, Scope, Send
from typing_extensions import override


class FeatureFlagConfig(BaseModel):
    api_base_url: str = "/platform"
    access_role_name: str | bool | None = None


class Config(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    feature_flag: FeatureFlagConfig


class FeatureFlagPatchRequest(TypedDict):
    name: str
    enabled: bool


@dataclass
class FeatureFlagPatch:
    name: str
    enabled: bool


class FeatureFlagRouterModule(ConfigurableModule, Generic[TFeatureFlag]):
    """
    An Injector module to provide an instance of a Feature Flag Router.

    :type ConfigurableModule: Enables loading of Ligare.web.middleware.feature_flags.Config config information
    :type Generic[TFeatureFlag]: The type of Feature Flag containing feature flag data
    """

    def __init__(
        self, t_feature_flag: type[FeatureFlagRouter[TFeatureFlag]] | None = None
    ) -> None:
        """
        Get an instance of the generic FeatureFlagRouterModule.

        :param type[FeatureFlagRouter[TFeatureFlag]] | None t_feature_flag: The type of Feature Flag Router this Injector module provides, defaults to None
        """
        self._t_feature_flag = type(self) if t_feature_flag is None else t_feature_flag
        super().__init__()

    @override
    @staticmethod
    def get_config_type() -> type[AbstractConfig]:
        """
        Get the Feature Flag Router Module configuration type.

        :return type[Ligare.web.middleware.feature_flags.Config]:
        """
        return Config

    @singleton
    @provider
    def _provide_feature_flag_router(
        self, injector: Injector
    ) -> FeatureFlagRouter[FeatureFlag]:
        """
        Provide the instance of FeatureFlagRouter[TFeatureFlag].

        :param Injector injector: The IoC container
        :return FeatureFlagRouter[FeatureFlag]: The FeatureFlagRouter[TFeatureFlag] instance
        """
        return cast(FeatureFlagRouter[FeatureFlag], injector.get(self._t_feature_flag))


class DBFeatureFlagRouterModule:
    def __new__(
        cls,
        feature_flag_table: type[FeatureFlagTableBase],
        bases: list[MetaBase | type[MetaBase]] | None = None,
    ):
        """
        An Injector module to work with Feature Flags stored in a database.

        :param type[FeatureFlagTableBase] feature_flag_table: The base table type representing columns the database table contains, and other aspects of SQLAlchemy Table object
        :param list[MetaBase  |  type[MetaBase]] | None bases: All MetaBase types an SQLAlchemy ScopedSession instance is responsible for, defaults to None
        :return _type_: _description_
        """

        class _DBFeatureFlagRouterModule(FeatureFlagRouterModule[DBFeatureFlag]):
            _feature_flag_table: type[FeatureFlagTableBase] = feature_flag_table
            _bases: list[MetaBase | type[MetaBase]] | None = bases

            def __init__(self) -> None:
                super().__init__(DBFeatureFlagRouter)

            @override
            def configure(self, binder: Binder) -> None:
                binder.install(ScopedSessionModule(self._bases))

            @singleton
            @provider
            def _provide_db_feature_flag_router(
                self, injector: Injector
            ) -> FeatureFlagRouter[DBFeatureFlag]:
                """
                Provide an instance of the FeatureFlagRouter for the DBFeatureFlag type.
                """
                return cast(
                    FeatureFlagRouter[DBFeatureFlag], injector.get(self._t_feature_flag)
                )

            @singleton
            @provider
            def _provide_db_feature_flag_router_table_base(
                self,
            ) -> type[FeatureFlagTableBase]:
                """
                Provide the base table type of the Feature Flag table.
                """
                return self._feature_flag_table

        return _DBFeatureFlagRouterModule


class CachingFeatureFlagRouterModule(FeatureFlagRouterModule[CachingFeatureFlag]):
    """
    An Injector module to work with Feature Flags in-memory.
    """

    def __init__(self) -> None:
        super().__init__(CachingFeatureFlagRouter)

    @singleton
    @provider
    def _provide_caching_feature_flag_router(
        self, injector: Injector
    ) -> FeatureFlagRouter[CachingFeatureFlag]:
        """
        Provide an instance of the FeatureFlagRouter for the CachingFeatureFlag type.
        """
        return cast(
            FeatureFlagRouter[CachingFeatureFlag], injector.get(self._t_feature_flag)
        )


P = ParamSpec("P")
R = TypeVar("R")


@inject
def _get_feature_flag_blueprint(app: Flask, config: FeatureFlagConfig, log: Logger):
    """
    Create and return a Flask Blueprint with API endpoints for querying and managing Feature Flags.

    :param Flask app: The registered Flask application this Blueprint will be applied to.
    :param FeatureFlagConfig config: The Feature Flag configuration type.
    :param Logger log:
    :raises ValueError:
    :return Blueprint:
    """
    feature_flag_blueprint = Blueprint(
        "feature_flag", __name__, url_prefix=f"{config.api_base_url}"
    )

    access_role = config.access_role_name

    def _login_required(require_flask_login: bool):
        """
        Decorate an API endpoint with the correct flask_login authentication
        method given the requirements of the API endpoint.

        require_flask_login is ignored if flask_login has been configured.

        If flask_login has _not_ been configured:
            * If require_flask_login is True, a warning is logged and the request is aborted with a 405 error
            * If require_flask_login is False, the endpoint function is executed

        :param bool require_flask_login: Determine whether flask_login must be configured for this endpoint to function
        :return _type_: _description_
        """

        def __login_required(
            fn: Callable[P, R],
        ) -> Callable[P, R]:
            authorization_implementation: Callable[..., Any]

            if access_role is False:
                authorization_implementation = fn
            # None means no roles were specified, but a session is still required
            elif access_role is None or access_role is True:
                authorization_implementation = login_required(fn)
            else:
                authorization_implementation = login_required([access_role])(fn)

            @wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not hasattr(app, "login_manager"):
                    if require_flask_login:
                        log.warning(
                            "The Feature Flag module expects flask_login to be configured in order to control access to feature flag modifications. flask_login has not been configured, so the Feature Flag modification API is disabled."
                        )

                        return abort(405)
                    else:
                        return fn(*args, **kwargs)
                return authorization_implementation(*args, **kwargs)

            return wrapper

        return __login_required

    @feature_flag_blueprint.route("/feature_flag", methods=("GET",))
    @_login_required(False)
    @inject
    def feature_flag(  # pyright: ignore[reportUnusedFunction]
        feature_flag_router: FeatureFlagRouter[FeatureFlag],
    ) -> dict[str, Any] | tuple[dict[str, Any], Literal[404]]:
        """
        Query Feature Flag values.
        This API does not require a Flask session.

        :param FeatureFlagRouter[FeatureFlag] feature_flag_router: The Feature Flag router type.
        :raises ValueError:
        :return dict[str, Any] | tuple[dict[str, Any], Literal[404]]:
        """
        request_query_names: list[str] | None = request.query_params.getlist("name")

        feature_flags: Sequence[FeatureFlag]
        missing_flags: set[str] | None = None
        if request_query_names is None or not request_query_names:
            feature_flags = feature_flag_router.get_feature_flags()
        elif isinstance(request_query_names, list):  # pyright: ignore[reportUnnecessaryIsInstance]
            feature_flags = feature_flag_router.get_feature_flags(request_query_names)
            missing_flags = set(request_query_names).difference(
                set([feature_flag.name for feature_flag in feature_flags])
            )
        else:
            raise ValueError("Unexpected type from Flask query parameters.")

        response: dict[str, Any] = {}
        problems: list[Any] = []

        if missing_flags is not None:
            for missing_flag in missing_flags:
                problems.append({
                    "title": "feature flag not found",
                    "detail": "Queried feature flag does not exist.",
                    "instance": missing_flag,
                    "status": 404,
                    "type": None,
                })
            response["problems"] = problems

        elif not feature_flags:
            problems.append({
                "title": "No feature flags found",
                "detail": "Queried feature flags do not exist.",
                "instance": "",
                "status": 404,
                "type": None,
            })
            response["problems"] = problems

        if feature_flags:
            response["data"] = feature_flags
            return response
        else:
            return response, 404

    @feature_flag_blueprint.route("/feature_flag", methods=("PATCH",))
    @_login_required(True)
    @inject
    async def feature_flag_patch(  # pyright: ignore[reportUnusedFunction]
        feature_flag_router: FeatureFlagRouter[FeatureFlag],
    ) -> dict[str, Any] | tuple[dict[str, Any], Literal[404]]:
        """
        Modify Feature Flag values.
        Requires a Flask session and appropriate User Role access. If access is not granted, HTTP status 405 is returned.

        :return dict[str, Any] | tuple[dict[str, Any], Literal[404]]:
        """
        feature_flags_request: list[FeatureFlagPatchRequest] = await request.json()

        feature_flags = [
            FeatureFlagPatch(name=flag["name"], enabled=flag["enabled"])
            for flag in feature_flags_request
        ]

        changes: list[Any] = []
        problems: list[Any] = []
        for flag in feature_flags:
            try:
                change = feature_flag_router.set_feature_is_enabled(
                    flag.name, flag.enabled
                )
                changes.append(change)
            except LookupError:
                problems.append({
                    "title": "feature flag not found",
                    "detail": "Feature flag to PATCH does not exist. It must be created first.",
                    "instance": flag.name,
                    "status": 404,
                    "type": None,
                })

        response: dict[str, Any] = {}

        if problems:
            response["problems"] = problems

        if changes:
            response["data"] = changes
            return response
        else:
            return response, 404

    return feature_flag_blueprint


class FeatureFlagMiddlewareModule(Module):
    """
    Enable the use of Feature Flags and a Feature Flag management API.
    """

    def __init__(
        self,
        feature_flag_router_module_type: type[FeatureFlagRouterModule[TFeatureFlag]],
    ) -> None:
        """
        Create the Injector module.

        :param type[FeatureFlagRouterModule[TFeatureFlag]] feature_flag_router_module_type:
        """
        super().__init__()
        self._feature_flag_router_module_type = feature_flag_router_module_type

    @override
    def configure(self, binder: Binder) -> None:
        binder.install(self._feature_flag_router_module_type())
        super().configure(binder)

    def register_middleware(self, app: FlaskApp):
        app.add_middleware(FeatureFlagMiddlewareModule.FeatureFlagMiddleware)

    class FeatureFlagMiddleware:
        """
        ASGI middleware for Feature Flags.

        This middleware create a Flask blueprint the enables a Feature Flag management API.
        """

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
            app: Flask,
            injector: Injector,
            log: Logger,
        ) -> None:
            async def wrapped_send(message: Any) -> None:
                # Only run during startup of the application
                if (
                    scope["type"] != "lifespan"
                    or message["type"] != "lifespan.startup.complete"
                    or not scope["app"]
                ):
                    return await send(message)

                log.debug("Registering FeatureFlag blueprint.")
                app.register_blueprint(
                    injector.call_with_injection(_get_feature_flag_blueprint)
                )
                log.debug("FeatureFlag blueprint registered.")

                return await send(message)

            await self._app(scope, receive, wrapped_send)
