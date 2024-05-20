import uuid
from typing import Literal, cast

import pytest
from BL_Python.identity.config import Config as RootSSOConfig
from BL_Python.identity.config import SSOConfig
from BL_Python.platform.dependency_injection import UserLoaderModule
from BL_Python.platform.identity import Role, User
from BL_Python.programming.config import AbstractConfig
from BL_Python.web.application import OpenAPIAppResult
from BL_Python.web.config import Config, WebSecurityCorsConfig
from BL_Python.web.middleware import bind_errorhandler
from BL_Python.web.middleware.consts import CORRELATION_ID_HEADER
from BL_Python.web.middleware.flask import (
    _get_correlation_id,  # pyright: ignore[reportPrivateUsage]
)
from BL_Python.web.middleware.flask import bind_requesthandler
from BL_Python.web.middleware.openapi.cors import CORSMiddlewareModule
from BL_Python.web.testing.create_app import (
    CreateOpenAPIApp,
    OpenAPIClientInjectorConfigurable,
    OpenAPIMockController,
    RequestConfigurable,
)
from connexion import FlaskApp
from connexion.middleware.exceptions import ExceptionMiddleware
from flask import Flask, abort
from injector import Module
from mock import MagicMock
from pytest_mock import MockerFixture
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp
from werkzeug.exceptions import BadRequest, HTTPException, Unauthorized


class TestOpenAPIMiddleware(CreateOpenAPIApp):
    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___register_api_response_handlers__sets_correlation_id_response_header_when_not_set_in_request_header(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        openapi_mock_controller.begin()
        flask_client = next(openapi_client_configurable(openapi_config))

        response = flask_client.client.get("/")

        assert response.headers[CORRELATION_ID_HEADER]
        _ = uuid.UUID(response.headers[CORRELATION_ID_HEADER])

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___register_api_response_handlers__sets_correlation_id_response_header_when_set_in_request_header(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        openapi_mock_controller.begin()
        flask_client = next(openapi_client_configurable(openapi_config))
        correlation_id = str(uuid.uuid4())
        response = flask_client.client.get(
            "/", headers={CORRELATION_ID_HEADER: correlation_id}
        )

        assert response.headers[CORRELATION_ID_HEADER] == correlation_id

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___register_api_response_handler__validates_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        correlation_id = "abc123"
        openapi_mock_controller.begin()
        flask_client = next(openapi_client_configurable(openapi_config))

        response = flask_client.client.get(
            "/", headers={CORRELATION_ID_HEADER: correlation_id}
        )

        assert response.status_code == 500

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__validates_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_request_configurable: RequestConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        correlation_id = "abc123"
        openapi_mock_controller.begin()
        with openapi_request_configurable(
            openapi_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
        ):
            with pytest.raises(
                ValueError, match="^badly formed hexadecimal UUID string$"
            ):
                _ = _get_correlation_id(MagicMock())

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__uses_existing_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_request_configurable: RequestConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        correlation_id = str(uuid.uuid4())
        openapi_mock_controller.begin()
        with openapi_request_configurable(
            openapi_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
        ):
            returned_correlation_id = _get_correlation_id(MagicMock())
            assert correlation_id == returned_correlation_id

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__sets_correlation_id(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_request_configurable: RequestConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        # app = FlaskApp("foo")
        openapi_config.logging.format = format

        openapi_mock_controller.begin()
        with openapi_request_configurable(openapi_config):
            correlation_id = _get_correlation_id(MagicMock())

            assert correlation_id
            _ = uuid.UUID(correlation_id)

    def test__bind_requesthandler__returns_decorated_flask_request_hook(self):
        app = FlaskApp("foo")

        flask_request_hook_mock = MagicMock()

        wrapped_decorator = bind_requesthandler(app.app, flask_request_hook_mock)
        _ = wrapped_decorator(lambda: None)

        assert flask_request_hook_mock.called

    def test__bind_requesthandler__calls_decorated_function_when_app_is_run(
        self,
        openapi_mock_controller: OpenAPIMockController,
    ):
        app = FlaskApp("foo")

        openapi_mock_controller.begin()

        flask_client = app.test_client()

        wrapped_handler_decorator = bind_requesthandler(app.app, Flask.before_request)
        request_handler_mock = MagicMock()
        _ = wrapped_handler_decorator(request_handler_mock)

        _ = flask_client.get("/")

        assert request_handler_mock.called

    @pytest.mark.parametrize(
        "code_or_exception,openapi_mock_controller",
        [(Exception, lambda: 1), (HTTPException, lambda: 1), (401, lambda: 1)],
        indirect=["openapi_mock_controller"],
    )
    def test__bind_errorhandler__binds_flask_errorhandler(
        self,
        code_or_exception: type[Exception] | int,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        flask_errorhandler_mock = mocker.patch("flask.Flask.errorhandler")

        def client_init_hook(app: OpenAPIAppResult):
            _ = bind_errorhandler(app.app_injector.app, code_or_exception)

        openapi_mock_controller.begin()
        _ = next(openapi_client_configurable(openapi_config, client_init_hook))

        flask_errorhandler_mock.assert_called_with(code_or_exception)

    @pytest.mark.parametrize(
        "code_or_exception_type,expected_exception_type,openapi_mock_controller",
        [
            (
                Exception,
                ZeroDivisionError,
                lambda: 1 / 0,  # 1/0 to raise an exception (any exception)
            ),
            (HTTPException, BadRequest, lambda: abort(400)),
            (401, Unauthorized, lambda: abort(401)),
        ],
        indirect=["openapi_mock_controller"],
    )
    def test__bind_errorhandler__calls_decorated_function_with_correct_error_when_error_occurs_during_request(
        self,
        code_or_exception_type: type[Exception] | int,
        expected_exception_type: type[Exception],
        openapi_mock_controller: OpenAPIMockController,
    ):
        app = FlaskApp("foo")
        application_errorhandler_mock = MagicMock()
        _ = bind_errorhandler(app, code_or_exception_type)(
            application_errorhandler_mock
        )

        openapi_mock_controller.begin()
        app.add_api("foo.yaml")

        flask_client = app.test_client()

        _ = flask_client.get("/", headers={"Host": "localhost:5000"})

        assert application_errorhandler_mock.called
        assert isinstance(
            application_errorhandler_mock.call_args[0][0], expected_exception_type
        )

    # FIXME just a temporary test as an example set up for testing SAML2
    def test__SAML2Middleware__something(
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

        def client_init_hook(app: OpenAPIAppResult):
            app.app_injector.flask_injector.injector.binder.bind(
                RootSSOConfig,
                to=RootSSOConfig(
                    sso=SSOConfig(
                        protocol="SAML2",
                        settings={
                            "relay_state": "http://localhost:5000/sso/redir",
                            "metadata_url": "http://example.org",
                            "metadata": "<xml />",
                        },
                    )
                ),
            )

        openapi_mock_controller.begin()
        app = next(
            openapi_client_configurable(openapi_config, client_init_hook, app_init_hook)
        )

        response = app.client.get("/saml/logout")

        # 401 for now because no real auth is configured.
        # if SSO was broken, 500 would return
        assert response.status_code == 401

    def test__CORSMiddlewareModule__adds_CORSMiddleware_to_app(
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
            application_modules.append(CORSMiddlewareModule)
            openapi_config.web.security.cors = WebSecurityCorsConfig(origins=["*"])

        openapi_mock_controller.begin()
        app = next(openapi_client_configurable(openapi_config, None, app_init_hook))

        flask_app = cast(FlaskApp, app.client.app)
        assert flask_app.middleware is not None
        assert flask_app.middleware.middleware_stack is not None
        assert CORSMiddleware in {
            type(middleware) for middleware in flask_app.middleware.middleware_stack
        }

    def test__CORSMiddlewareModule__adds_CORSMiddleware_before_ExceptionMiddleware(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
    ):
        def app_init_hook(
            application_configs: list[type[AbstractConfig]],
            application_modules: list[Module | type[Module]],
        ):
            application_modules.append(CORSMiddlewareModule)
            openapi_config.web.security.cors = WebSecurityCorsConfig(origins=["*"])

        openapi_mock_controller.begin()
        app = next(openapi_client_configurable(openapi_config, None, app_init_hook))

        flask_app = cast(FlaskApp, app.client.app)
        assert flask_app.middleware is not None
        assert flask_app.middleware.middleware_stack is not None
        middleware_types = [
            type(middleware) for middleware in flask_app.middleware.middleware_stack
        ]

        # fmt: off
        assert\
            middleware_types.index(cast(ASGIApp, CORSMiddleware))\
          < middleware_types.index(cast(ASGIApp, ExceptionMiddleware))
        # fmt: on

    def test__CORSMiddlewareModule__uses_WebSecurityCorsConfig_values(
        self,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
    ):
        def app_init_hook(
            application_configs: list[type[AbstractConfig]],
            application_modules: list[Module | type[Module]],
        ):
            application_modules.append(CORSMiddlewareModule)
            openapi_config.web.security.cors = WebSecurityCorsConfig(
                origins=["*"], allow_credentials=True
            )

        openapi_mock_controller.begin()
        app = next(openapi_client_configurable(openapi_config, None, app_init_hook))

        flask_app = cast(FlaskApp, app.client.app)
        assert flask_app.middleware is not None
        assert flask_app.middleware.middleware_stack is not None
        cors_middleware = cast(
            CORSMiddleware,
            next(
                filter(
                    lambda a: isinstance(a, CORSMiddleware),
                    flask_app.middleware.middleware_stack,
                )
            ),
        )

        assert (
            cors_middleware.allow_methods
            == openapi_config.web.security.cors.allow_methods
        )
        assert cors_middleware.allow_origins == openapi_config.web.security.cors.origins
        assert all([
            header in cors_middleware.allow_headers
            for header in openapi_config.web.security.cors.allow_headers
        ])
        assert (
            cors_middleware.preflight_headers["Access-Control-Allow-Credentials"]  # pyright: ignore[reportUnknownMemberType]
            == "true"
        )
