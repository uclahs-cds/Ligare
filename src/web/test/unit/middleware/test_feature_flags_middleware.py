import uuid
from typing import Literal

import pytest
from BL_Python.platform.dependency_injection import UserLoaderModule
from BL_Python.platform.feature_flag.db_feature_flag_router import DBFeatureFlagRouter
from BL_Python.platform.feature_flag.db_feature_flag_router import (
    FeatureFlag as DBFeatureFlag,
)
from BL_Python.platform.feature_flag.feature_flag_router import FeatureFlagRouter
from BL_Python.platform.identity import Role, User
from BL_Python.programming.config import AbstractConfig
from BL_Python.web.application import OpenAPIAppResult
from BL_Python.web.config import Config
from BL_Python.web.middleware import bind_errorhandler
from BL_Python.web.middleware.consts import CORRELATION_ID_HEADER
from BL_Python.web.middleware.feature_flags import Config as RootFeatureFlagConfig
from BL_Python.web.middleware.feature_flags import (
    DBFeatureFlagRouterModule,
    FeatureFlagConfig,
    FeatureFlagMiddlewareModule,
    FeatureFlagRouterModule,
)
from BL_Python.web.middleware.flask import (
    _get_correlation_id,  # pyright: ignore[reportPrivateUsage]
)
from BL_Python.web.middleware.flask import bind_requesthandler
from BL_Python.web.testing.create_app import (
    CreateOpenAPIApp,
    OpenAPIClientInjectorConfigurable,
    OpenAPIMockController,
    RequestConfigurable,
)
from connexion import FlaskApp
from flask import Flask, abort
from injector import Module
from mock import MagicMock
from pytest_mock import MockerFixture
from werkzeug.exceptions import BadRequest, HTTPException, Unauthorized


class TestFeatureFlagsMiddleware(CreateOpenAPIApp):
    def test__FeatureFlagMiddleware__feature_flag_api_get_requires_user_session(
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
            application_modules.append(DBFeatureFlagRouterModule)
            application_configs.append(RootFeatureFlagConfig)
            application_modules.append(FeatureFlagMiddlewareModule())

        def client_init_hook(app: OpenAPIAppResult):
            feature_flag_config = FeatureFlagConfig(
                access_role_name="Operator",
                api_base_url="/server",  # the default
            )
            root_feature_flag_config = RootFeatureFlagConfig(
                feature_flag=feature_flag_config
            )
            app.app_injector.flask_injector.injector.binder.bind(
                FeatureFlagConfig, to=feature_flag_config
            )
            app.app_injector.flask_injector.injector.binder.bind(
                RootFeatureFlagConfig, to=root_feature_flag_config
            )

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(openapi_config, client_init_hook, app_init_hook)
        )

        response = app.client.get("/server/feature_flag")

        # 401 for now because no real auth is configured.
        # if SSO was broken, 500 would return
        assert response.status_code == 401

    def test__FeatureFlagMiddleware__something(
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
            application_modules.append(
                UserLoaderModule(
                    loader=User,  # pyright: ignore[reportArgumentType]
                    roles=Role,  # pyright: ignore[reportArgumentType]
                    user_table=MagicMock(),  # pyright: ignore[reportArgumentType]
                    role_table=MagicMock(),  # pyright: ignore[reportArgumentType]
                    bases=[],
                )
            )
            application_modules.append(DBFeatureFlagRouterModule)
            application_configs.append(RootFeatureFlagConfig)
            application_modules.append(FeatureFlagMiddlewareModule())

        def client_init_hook(app: OpenAPIAppResult):
            feature_flag_config = FeatureFlagConfig(
                access_role_name="Operator",
                api_base_url="/server",  # the default
            )
            root_feature_flag_config = RootFeatureFlagConfig(
                feature_flag=feature_flag_config
            )
            app.app_injector.flask_injector.injector.binder.bind(
                FeatureFlagConfig, to=feature_flag_config
            )
            app.app_injector.flask_injector.injector.binder.bind(
                RootFeatureFlagConfig, to=root_feature_flag_config
            )

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(openapi_config, client_init_hook, app_init_hook)
        )

        response = app.client.get("/server/feature_flag")

        # 401 for now because no real auth is configured.
        # if SSO was broken, 500 would return
        assert response.status_code == 401
