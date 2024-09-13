from dataclasses import dataclass
from enum import auto
from typing import Generic, Sequence, TypeVar

import pytest
from BL_Python.platform.dependency_injection import UserLoaderModule
from BL_Python.platform.feature_flag import FeatureFlag, caching_feature_flag_router
from BL_Python.platform.feature_flag.caching_feature_flag_router import (
    CachingFeatureFlagRouter,
)
from BL_Python.platform.feature_flag.feature_flag_router import FeatureFlagRouter
from BL_Python.platform.identity.user_loader import Role as LoaderRole
from BL_Python.programming.config import AbstractConfig
from BL_Python.web.application import CreateAppResult, OpenAPIAppResult
from BL_Python.web.config import Config
from BL_Python.web.middleware.feature_flags import (
    CachingFeatureFlagRouterModule,
    FeatureFlagConfig,
    FeatureFlagMiddlewareModule,
)
from BL_Python.web.testing.create_app import (
    CreateOpenAPIApp,
    OpenAPIClientInjectorConfigurable,
    OpenAPIMockController,
)
from connexion import FlaskApp
from flask_login import UserMixin
from injector import Module
from mock import MagicMock
from pytest_mock import MockerFixture
from typing_extensions import override


@dataclass
class UserId:
    user_id: int
    username: str


class Role(LoaderRole):
    User = auto()
    Administrator = auto()
    Operator = auto()

    @staticmethod
    def items():
        return Role.__members__.items()


TRole = TypeVar("TRole", bound=Role, covariant=True)


class User(UserMixin, Generic[TRole]):
    """
    Represents the user object stored in a session.
    """

    id: UserId
    roles: Sequence[TRole]

    @override
    def get_id(self):
        """
        Override the UserMixin.get_id so the username is returned instead of `id` (the dataclass)
        when `flask_login.login_user` calls this method to assign the
        session `_user_id` key.
        """
        return str(self.id.username)

    @override
    def __init__(self, id: UserId, roles: Sequence[TRole] | None = None):
        """
        Create a new user with the given user name or id, and a list of roles.
        If roles are not given, an empty list is assigned by default.
        """
        super().__init__()

        if roles is None:
            roles = []

        self.id = id
        self.roles = roles


class TestFeatureFlagsMiddleware(CreateOpenAPIApp):
    def _user_session_app_init_hook(
        self,
        application_configs: list[type[AbstractConfig]],
        application_modules: list[Module | type[Module]],
    ):
        application_modules.append(
            UserLoaderModule(
                loader=User,  # pyright: ignore[reportArgumentType]
                roles=Role,
                user_table=MagicMock(),  # pyright: ignore[reportArgumentType]
                role_table=MagicMock(),  # pyright: ignore[reportArgumentType]
                bases=[],
            )
        )
        application_modules.append(CachingFeatureFlagRouterModule)
        application_modules.append(FeatureFlagMiddlewareModule())

    def test__FeatureFlagMiddleware__feature_flag_api_GET_requires_user_session(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
    ):
        def app_init_hook(
            application_configs: list[type[AbstractConfig]],
            application_modules: list[Module | type[Module]],
        ):
            application_modules.append(CachingFeatureFlagRouterModule)
            application_modules.append(FeatureFlagMiddlewareModule())

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(openapi_config, app_init_hook=app_init_hook)
        )

        response = app.client.get("/server/feature_flag")

        # 401 for now because no real auth is configured.
        # if SSO was broken, 500 would return
        assert response.status_code == 401

    def test__FeatureFlagMiddleware__feature_flag_api_GET_gets_feature_flags_when_user_has_session(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        get_feature_flag_mock = mocker.patch(
            "BL_Python.web.middleware.feature_flags.CachingFeatureFlagRouter.get_feature_flags",
            return_value=[],
        )

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config, app_init_hook=self._user_session_app_init_hook
            )
        )

        with self.get_authenticated_request_context(
            app,
            User,  # pyright: ignore[reportArgumentType]
            mocker,
        ):
            response = app.client.get("/server/feature_flag")

        assert response.status_code == 404
        get_feature_flag_mock.assert_called_once()

    @pytest.mark.parametrize("has_role", [True, False])
    def test__FeatureFlagMiddleware__feature_flag_api_GET_requires_specified_role(
        self,
        has_role: bool,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        get_feature_flag_mock = mocker.patch(
            "BL_Python.web.middleware.feature_flags.CachingFeatureFlagRouter.get_feature_flags",
            return_value=[],
        )

        def client_init_hook(app: OpenAPIAppResult):
            feature_flag_config = FeatureFlagConfig(
                access_role_name="Operator",
                api_base_url="/server",  # the default
            )
            app.app_injector.flask_injector.injector.binder.bind(
                FeatureFlagConfig, to=feature_flag_config
            )

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config, client_init_hook, self._user_session_app_init_hook
            )
        )

        with self.get_authenticated_request_context(
            app,
            User,  # pyright: ignore[reportArgumentType]
            mocker,
            [Role.Operator] if has_role else [],
        ):
            response = app.client.get("/server/feature_flag")

        if has_role:
            assert response.status_code == 404
            get_feature_flag_mock.assert_called_once()
        else:
            assert response.status_code == 401
            get_feature_flag_mock.assert_not_called()

    def test__FeatureFlagMiddleware__feature_flag_api_GET_returns_no_feature_flags_when_none_exist(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config, app_init_hook=self._user_session_app_init_hook
            )
        )

        with self.get_authenticated_request_context(
            app,
            User,  # pyright: ignore[reportArgumentType]
            mocker,
        ):
            response = app.client.get("/server/feature_flag")

        assert response.status_code == 404
        response_json = response.json()
        assert (problems := response_json.get("problems", None)) is not None
        assert len(problems) == 1
        assert (title := problems[0].get("title", None)) is not None
        assert title == "No feature flags found"

    def test__FeatureFlagMiddleware__feature_flag_api_GET_returns_feature_flags_when_they_exist(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        def client_init_hook(app: CreateAppResult[FlaskApp]):
            caching_feature_flag_router = app.app_injector.flask_injector.injector.get(
                FeatureFlagRouter[FeatureFlag]
            )
            _ = caching_feature_flag_router.set_feature_is_enabled("foo_feature", True)

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config,
                client_init_hook,
                self._user_session_app_init_hook,
            )
        )

        with self.get_authenticated_request_context(
            app,
            User,  # pyright: ignore[reportArgumentType]
            mocker,
        ):
            response = app.client.get("/server/feature_flag")

        assert response.status_code == 200
        response_json = response.json()
        assert (data := response_json.get("data", None)) is not None
        assert len(data) == 1
        assert data[0].get("enabled", None) is True
        assert data[0].get("name", None) == "foo_feature"
