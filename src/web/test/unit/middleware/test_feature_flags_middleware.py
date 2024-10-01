from dataclasses import dataclass
from enum import auto
from typing import Generic, Sequence, TypeVar

import pytest
from connexion import FlaskApp
from flask_login import UserMixin
from injector import Module
from Ligare.platform.dependency_injection import UserLoaderModule
from Ligare.platform.feature_flag import FeatureFlag
from Ligare.platform.feature_flag.feature_flag_router import FeatureFlagRouter
from Ligare.platform.identity.user_loader import Role as LoaderRole
from Ligare.programming.config import AbstractConfig
from Ligare.web.application import CreateAppResult, OpenAPIAppResult
from Ligare.web.config import Config
from Ligare.web.middleware.feature_flags import (
    CachingFeatureFlagRouterModule,
    FeatureFlagConfig,
    FeatureFlagMiddlewareModule,
)
from Ligare.web.testing.create_app import (
    CreateOpenAPIApp,
    OpenAPIClientInjectorConfigurable,
    OpenAPIMockController,
)
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

    def test__FeatureFlagMiddleware__feature_flag_api_GET_requires_user_session_when_flask_login_is_configured(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        def app_init_hook(
            application_configs: list[type[AbstractConfig]],
            application_modules: list[Module | type[Module]],
        ):
            application_modules.append(CachingFeatureFlagRouterModule)
            application_modules.append(FeatureFlagMiddlewareModule())

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config,
                app_init_hook=app_init_hook,
            )
        )

        response = app.client.get("/platform/feature_flag")

        assert response.status_code == 401

    @pytest.mark.parametrize(
        "flask_login_is_configured,user_has_session",
        [[True, True], [False, True], [False, False]],
    )
    def test__FeatureFlagMiddleware__feature_flag_api_GET_gets_feature_flags(
        self,
        flask_login_is_configured: bool,
        user_has_session: bool,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        def app_init_hook(
            application_configs: list[type[AbstractConfig]],
            application_modules: list[Module | type[Module]],
        ):
            if not flask_login_is_configured:
                application_modules.clear()
            application_modules.append(CachingFeatureFlagRouterModule)
            application_modules.append(FeatureFlagMiddlewareModule())

        def client_init_hook(app: CreateAppResult[FlaskApp]):
            caching_feature_flag_router = app.app_injector.flask_injector.injector.get(
                FeatureFlagRouter[FeatureFlag]
            )
            _ = caching_feature_flag_router.set_feature_is_enabled("foo_feature", True)

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config,
                client_init_hook=client_init_hook,
                app_init_hook=app_init_hook,
            )
        )

        if user_has_session:
            with self.get_authenticated_request_context(
                app,
                User,  # pyright: ignore[reportArgumentType]
                mocker,
            ):
                response = app.client.get("/platform/feature_flag")
        else:
            response = app.client.get("/platform/feature_flag")

        assert response.status_code == 200
        response_json = response.json()
        assert (data := response_json.get("data", None)) is not None
        assert len(data) == 1
        assert (name := data[0].get("name", None)) is not None
        assert (enabled := data[0].get("enabled", None)) is not None
        assert name == "foo_feature"
        assert enabled == True

    @pytest.mark.parametrize("has_role", [True, False])
    def test__FeatureFlagMiddleware__feature_flag_api_GET_requires_specified_role_when_flask_login_is_configured(
        self,
        has_role: bool,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        get_feature_flag_mock = mocker.patch(
            "Ligare.web.middleware.feature_flags.CachingFeatureFlagRouter.get_feature_flags",
            return_value=[],
        )

        def client_init_hook(app: OpenAPIAppResult):
            feature_flag_config = FeatureFlagConfig(
                access_role_name="Operator",
                api_base_url="/platform",  # the default
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
            response = app.client.get("/platform/feature_flag")

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
            response = app.client.get("/platform/feature_flag")

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
            response = app.client.get("/platform/feature_flag")

        assert response.status_code == 200
        response_json = response.json()
        assert (data := response_json.get("data", None)) is not None
        assert len(data) == 1
        assert data[0].get("enabled", None) is True
        assert data[0].get("name", None) == "foo_feature"

    @pytest.mark.parametrize(
        "query_flags", ["bar_feature", ["foo_feature", "baz_feature"]]
    )
    def test__FeatureFlagMiddleware__feature_flag_api_GET_returns_specific_feature_flags_when_they_exist(
        self,
        query_flags: str | list[str],
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
            _ = caching_feature_flag_router.set_feature_is_enabled("bar_feature", False)
            _ = caching_feature_flag_router.set_feature_is_enabled("baz_feature", True)

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
            response = app.client.get(
                "/platform/feature_flag", params={"name": query_flags}
            )

        assert response.status_code == 200
        response_json = response.json()
        assert (data := response_json.get("data", None)) is not None
        if isinstance(query_flags, str):
            assert len(data) == 1
            assert data[0].get("enabled", None) is False
            assert data[0].get("name", None) == query_flags
        else:
            assert len(data) == len(query_flags)
            for i, flag in enumerate(query_flags):
                assert data[i].get("enabled", None) is True
                assert data[i].get("name", None) == flag

    @pytest.mark.parametrize(
        "flask_login_is_configured,user_has_session,error_code",
        [[True, False, 401], [False, True, 405], [False, False, 405]],
    )
    def test__FeatureFlagMiddleware__feature_flag_api_PATCH_requires_user_session_and_flask_login(
        self,
        flask_login_is_configured: bool,
        user_has_session: bool,
        error_code: int,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        set_feature_flag_mock = mocker.patch(
            "Ligare.web.middleware.feature_flags.CachingFeatureFlagRouter.set_feature_is_enabled",
            return_value=[],
        )

        def app_init_hook(
            application_configs: list[type[AbstractConfig]],
            application_modules: list[Module | type[Module]],
        ):
            if not flask_login_is_configured:
                application_modules.clear()
            application_modules.append(CachingFeatureFlagRouterModule)
            application_modules.append(FeatureFlagMiddlewareModule())

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(
                openapi_config,
                app_init_hook=app_init_hook,
            )
        )

        if user_has_session:
            with self.get_authenticated_request_context(
                app,
                User,  # pyright: ignore[reportArgumentType]
                mocker,
            ):
                response = app.client.patch(
                    "/platform/feature_flag",
                    json=[{"name": "foo_feature", "enabled": False}],
                )
        else:
            response = app.client.patch(
                "/platform/feature_flag",
                json=[{"name": "foo_feature", "enabled": False}],
            )

        assert response.status_code == error_code
        set_feature_flag_mock.assert_not_called()

    def test__FeatureFlagMiddleware__feature_flag_api_PATCH_modifies_feature_flag_when_user_has_session_and_flask_login_is_configured(
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
            response = app.client.patch(
                "/platform/feature_flag",
                json=[{"name": "foo_feature", "enabled": False}],
            )

        assert response.status_code == 200
        response_json = response.json()
        assert (data := response_json.get("data", None)) is not None
        assert len(data) == 1
        assert data[0].get("name", None) == "foo_feature"
        assert data[0].get("new_value", None) == False
        assert data[0].get("old_value", None) == True
