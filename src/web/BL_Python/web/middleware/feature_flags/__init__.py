# """
# Server blueprint
# Non-API specific endpoints for application management
# """
#
# from typing import Any, Sequence, cast
#
# import flask
# from BL_Python.platform.feature_flag import FeatureFlagChange, FeatureFlagRouter
# from BL_Python.web.middleware.sso import login_required
# from flask import request
# from injector import inject
#
# from CAP import __version__
# from CAP.app.models.user.role import Role as UserRole
# from CAP.app.schemas.platform.get_request_feature_flag_schema import (
#    GetResponseFeatureFlagSchema,
# )
# from CAP.app.schemas.platform.patch_request_feature_flag_schema import (
#    PatchRequestFeatureFlag,
#    PatchRequestFeatureFlagSchema,
#    PatchResponseFeatureFlagSchema,
# )
# from CAP.app.schemas.platform.response_problem_schema import (
#    ResponseProblem,
#    ResponseProblemSchema,
# )
#
# _FEATURE_FLAG_NOT_FOUND_PROBLEM_TITLE = "Feature Flag Not Found"
# _FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS = 404
############
from logging import Logger
from typing import Any, Callable, Generic, Sequence, cast

from BL_Python.platform.feature_flag.caching_feature_flag_router import (
    FeatureFlag as CachingFeatureFlag,
)
from BL_Python.platform.feature_flag.db_feature_flag_router import DBFeatureFlagRouter
from BL_Python.platform.feature_flag.db_feature_flag_router import (
    FeatureFlag as DBFeatureFlag,
)
from BL_Python.platform.feature_flag.db_feature_flag_router import (
    FeatureFlagTable,
    FeatureFlagTableBase,
)
from BL_Python.platform.feature_flag.feature_flag_router import (
    FeatureFlag,
    FeatureFlagRouter,
    TFeatureFlag,
)
from BL_Python.platform.identity.user_loader import Role, UserId, UserLoader, UserMixin
from BL_Python.programming.config import AbstractConfig
from BL_Python.web.middleware.sso import login_required
from connexion import FlaskApp
from flask import Blueprint, Flask, request
from injector import Binder, Injector, Module, inject, provider
from pydantic import BaseModel

# from sqlalchemy.orm.scoping import ScopedSession
from starlette.types import ASGIApp, Receive, Scope, Send
from typing_extensions import override


class FeatureFlagConfig(BaseModel):
    api_base_url: str = "/server"
    access_role_name: str | None = None  # "Operator"


class Config(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    feature_flag: FeatureFlagConfig


# TODO consider having the DI registration log a warning if
# an interface is being overwritten
class FeatureFlagRouterModule(Module, Generic[TFeatureFlag]):
    def __init__(self, t_feature_flag: type[FeatureFlagRouter[TFeatureFlag]]) -> None:
        self._t_feature_flag = t_feature_flag
        super().__init__()

    @provider
    def _provide_feature_flag_router(
        self, injector: Injector
    ) -> FeatureFlagRouter[FeatureFlag]:
        return injector.get(self._t_feature_flag)


class DBFeatureFlagRouterModule(FeatureFlagRouterModule[DBFeatureFlag]):
    def __init__(self) -> None:
        super().__init__(DBFeatureFlagRouter)

    @provider
    def _provide_db_feature_flag_router(
        self, injector: Injector
    ) -> FeatureFlagRouter[DBFeatureFlag]:
        return injector.get(self._t_feature_flag)

    @provider
    def _provide_db_feature_flag_router_table_base(self) -> type[FeatureFlagTableBase]:
        # FeatureFlagTable is a FeatureFlagTableBase provided through
        # SQLAlchemy's declarative meta API
        return cast(type[FeatureFlagTableBase], FeatureFlagTable)


class CachingFeatureFlagRouterModule(FeatureFlagRouterModule[CachingFeatureFlag]):
    @provider
    def _provide_caching_feature_flag_router(
        self, injector: Injector
    ) -> FeatureFlagRouter[CachingFeatureFlag]:
        return injector.get(self._t_feature_flag)


def get_feature_flag_blueprint(
    config: FeatureFlagConfig, access_roles: list[Role] | bool = True
):
    feature_flag_blueprint = Blueprint(
        "feature_flag", __name__, url_prefix=f"{config.api_base_url}"
    )

    # access_role = config.feature_flag.access_role_name
    # convert this enum somehow

    def _login_required(fn: Callable[..., Any]):
        if access_roles is False:
            return fn

        if access_roles is True:
            return login_required(fn)

        return login_required(access_roles)(fn)

    @feature_flag_blueprint.route("/feature_flag", methods=("GET",))
    @_login_required
    @inject
    def feature_flag(feature_flag_router: FeatureFlagRouter[FeatureFlag]):
        request_query_names: list[str] | None = request.args.to_dict(flat=False).get(
            "name"
        )

        feature_flags: Sequence[FeatureFlag]
        missing_flags: set[str] | None = None
        if request_query_names is None:
            feature_flags = feature_flag_router.get_feature_flags()
        elif isinstance(request_query_names, list):  # pyright: ignore[reportUnnecessaryIsInstance]
            feature_flags = feature_flag_router.get_feature_flags(request_query_names)
            missing_flags = set(request_query_names).difference(
                set([feature_flag.name for feature_flag in feature_flags])
            )
        else:
            raise ValueError("Unexpected type from Flask query parameters.")

        response: dict[str, Any] = {}

        if missing_flags:
            # problems: list[ResponseProblem] = []
            problems: list[Any] = []
            for missing_flag in missing_flags:
                problems.append(
                    # ResponseProblem(
                    {
                        "title": "feature flag not found",  # _FEATURE_FLAG_NOT_FOUND_PROBLEM_TITLE,
                        "detail": "Queried feature flag does not exist.",
                        "instance": missing_flag,
                        "status": 404,  # _FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS,
                        "type": None,
                    }
                    # )
                )
            response["problems"] = (
                problems  # ResponseProblemSchema().dump(problems, many=True)
            )

        if feature_flags:
            response["data"] = feature_flags  # GetResponseFeatureFlagSchema().dump(
            #    feature_flags, many=True
            # )
            return response
        else:
            return response, 404  # _FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS

    #
    #
    ## @server_blueprint.route("/server/feature_flag", methods=("PATCH",))
    # @login_required([UserRole.Operator])
    # @inject
    # def feature_flag_patch(feature_flag_router: FeatureFlagRouter[DBFeatureFlag]):
    #    post_request_feature_flag_schema = PatchRequestFeatureFlagSchema()
    #
    #    feature_flags: list[PatchRequestFeatureFlag] = cast(
    #        list[PatchRequestFeatureFlag],
    #        post_request_feature_flag_schema.load(
    #            flask.request.json,  # pyright: ignore[reportArgumentType] why is `flask.request.json` wrong here?
    #            many=True,
    #        ),
    #    )
    #
    #    changes: list[FeatureFlagChange] = []
    #    problems: list[ResponseProblem] = []
    #    for flag in feature_flags:
    #        try:
    #            change = feature_flag_router.set_feature_is_enabled(flag.name, flag.enabled)
    #            changes.append(change)
    #        except LookupError:
    #            problems.append(
    #                ResponseProblem(
    #                    title=_FEATURE_FLAG_NOT_FOUND_PROBLEM_TITLE,
    #                    detail="Feature flag to PATCH does not exist. It must be created first.",
    #                    instance=flag.name,
    #                    status=_FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS,
    #                    type=None,
    #                )
    #            )
    #
    #    response: dict[str, Any] = {}
    #
    #    if problems:
    #        response["problems"] = ResponseProblemSchema().dump(problems, many=True)
    #
    #    if changes:
    #        response["data"] = PatchResponseFeatureFlagSchema().dump(changes, many=True)
    #        return response
    #    else:
    #        return response, _FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS
    #
    return feature_flag_blueprint


# class FeatureFlagModule(Module):
#    def __init__(self):
#        """ """
#        super().__init__()


class FeatureFlagMiddlewareModule(Module):
    @override
    def __init__(self, access_roles: list[Role] | bool = True) -> None:
        self._access_roles = access_roles
        super().__init__()

    @override
    def configure(self, binder: Binder) -> None:
        super().configure(binder)

    def register_middleware(self, app: FlaskApp):
        app.add_middleware(FeatureFlagMiddlewareModule.FeatureFlagMiddleware)

    class FeatureFlagMiddleware:
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
                    get_feature_flag_blueprint(injector.get(FeatureFlagConfig))
                )
                log.debug("FeatureFlag blueprint registered.")

                return await send(message)

            await self._app(scope, receive, wrapped_send)
