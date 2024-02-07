import importlib
import logging
import sys
from collections import defaultdict
from contextlib import _GeneratorContextManager  # pyright: ignore[reportPrivateUsage]
from contextlib import ExitStack
from dataclasses import dataclass
from functools import lru_cache
from types import ModuleType
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    NamedTuple,
    Protocol,
    TypeVar,
    cast,
)

import json_logging
import pytest
import yaml
from BL_Python.programming.str import get_random_str
from BL_Python.web.application import (
    App,
    AppInjector,
    FlaskAppInjector,
    OpenAPIAppInjector,
    T_app,
)
from BL_Python.web.config import (
    Config,
    FlaskConfig,
    FlaskOpenApiConfig,
    FlaskSessionConfig,
    FlaskSessionCookieConfig,
)
from BL_Python.web.encryption import encrypt_flask_cookie
from connexion import FlaskApp
from connexion.apps.abstract import TestClient
from flask import Flask, Request, Response
from flask.ctx import RequestContext
from flask.sessions import SecureCookieSession
from flask.testing import FlaskClient
from flask_injector import FlaskInjector
from mock import MagicMock
from pytest import FixtureRequest
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType
from starlette.middleware.trustedhost import TrustedHostMiddleware

TFlaskClient = FlaskClient | TestClient
T_flask_client = TypeVar("T_flask_client", bound=TFlaskClient)


@dataclass
class ClientInjector(Generic[T_flask_client]):
    """
    Flask test client and IoC container for the application
    created by PyTest fixtures.
    """

    client: T_flask_client
    injector: FlaskInjector


class AppGetter(Protocol[T_app]):
    """
    A callable that instantiates a Flask application
    and returns the application with its IoC container.
    """

    def __call__(self) -> AppInjector[T_app]: ...


TAppInitHook = Callable[[AppInjector[T_app]], None] | None


class ClientInjectorConfigurable(Protocol[T_app, T_flask_client]):
    """
    Get a Flask test client using the specified application configuration.

    Args
    ------
        config: `Config` The custom application configuration used to instantiate the Flask app.

    Returns
    ------
        `FlaskClientInjector[T_flask_client]`
    """

    def __call__(
        self,
        config: Config,
        app_init_hook: TAppInitHook[T_app] | None = None,
    ) -> ClientInjector[T_flask_client]: ...


FlaskClientInjectorConfigurable = ClientInjectorConfigurable[Flask, FlaskClient]
OpenAPIClientInjectorConfigurable = ClientInjectorConfigurable[FlaskApp, TestClient]
FlaskClientInjector = ClientInjector[FlaskClient]
OpenAPIClientInjector = ClientInjector[TestClient]
OpenAPIAppInitHook = TAppInitHook[FlaskApp]


class RequestConfigurable(Protocol):
    """
    Get a Flask request context, creating a Flask test client
    that uses the specified application configuration and,
    optionally, specific request context arguments.

    This creates the Flask test client using the `ClientConfigurable` fixture.

    Args
    ------
        config: `Config` The custom application configuration used to instantiate the Flask app.
        request_context_args: `dict[Any, Any] | None = None` The optional request context arguments
            set up in the request context. These may contain, for example, request headers,
            authentication credentials, etc.

    Returns
    ------
        `RequestContext`
    """

    def __call__(
        self, config: Config, request_context_args: dict[Any, Any] | None = None
    ) -> RequestContext: ...


class TestSessionMiddleware:
    _app: Flask

    def __init__(self, app: Flask) -> None:  # pyright: ignore[reportMissingSuperCall]
        self._app = app

    def __call__(
        self, environ: dict[Any, Any], start_response: Callable[[Request], Response]
    ) -> Any:
        from flask import request, session

        session["_id"] = get_random_str()

        return start_response(request)


class MockController(NamedTuple):
    begin: Callable[[], None]
    end: Callable[[], None]


class OpenAPIMockController(MockController):
    """
    A fixture used to mock some internals of Connexion to enable
    GET requests in tests.

    An OpenAPI application should be created, and any bindings managed,
    before calling `openapi_mock.begin()`. Once `begin()` is called,
    changes to the application may result in undefined behavior.

    `openapi_mock.end()` is called after the test finishes, and may also
    be explicitly called in the test.

    Args
    ------
        `Callable[[], Response]` A method used as the request handler for GET requests set to `/`.
        This parameter is set through parametrization:

        ```python
        @pytest.mark.parametrize("openapi_mock", lambda: {}, indirect=["openapi_mock"])
        def test_my_test(openapi_mock: OpenAPIMockController):
            ...
        ```

    Returns
    ------
        `RequestContext`
    """


class CreateApp:
    _automatic_mocks: dict[str, MagicMock] = defaultdict()

    def _basic_config(self) -> Config:
        return Config(
            flask=FlaskConfig(
                app_name="test_app",
                env="Testing",
                session=FlaskSessionConfig(
                    cookie=FlaskSessionCookieConfig(secret_key=get_random_str())
                ),
            )
        )

    def _openapi_config(self) -> Config:
        config = self._basic_config()
        cast(FlaskConfig, config.flask).openapi = FlaskOpenApiConfig(
            spec_path="config.toml", use_swagger=False
        )
        return config

    @pytest.fixture()
    def basic_config(self):
        return self._basic_config()

    @pytest.fixture()
    def openapi_config(self):
        return self._openapi_config()

    def __get_basic_flask_app(
        self, config: Config, mocker: MockerFixture
    ) -> Generator[FlaskAppInjector, Any, None]:
        # prevents the creation of a Connexion application
        if config.flask is not None:
            config.flask.openapi = None

        with mocker.patch(
            "BL_Python.web.application.load_config",
            return_value=config,
        ):
            app = App[Flask].create()
            yield app.app_injector

    def __get_openapi_app(
        self, config: Config, mocker: MockerFixture
    ) -> Generator[OpenAPIAppInjector, Any, None]:
        # prevents the creation of a Connexion application
        if config.flask is None or config.flask.openapi is None:
            raise Exception(
                "[openapi] not set in config. Cannot create OpenAPI test client."
            )

        with mocker.patch(
            "BL_Python.web.application.load_config",
            return_value=config,
        ):
            app = App[FlaskApp].create()
            yield app.app_injector

    @pytest.fixture()
    def _get_basic_flask_app(
        self, basic_config: Config, mocker: MockerFixture
    ) -> FlaskAppInjector:
        return next(self.__get_basic_flask_app(basic_config, mocker))

    @pytest.fixture()
    def _get_openapi_app(
        self, openapi_config: Config, mocker: MockerFixture
    ) -> OpenAPIAppInjector:
        return next(self.__get_openapi_app(openapi_config, mocker))

    def _flask_client(
        self, flask_app_getter: AppGetter[Flask]
    ) -> Generator[FlaskClientInjector, Any, None]:
        with ExitStack() as stack:
            result = flask_app_getter()

            if not isinstance(
                result, AppInjector
            ) or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                result.app, Flask
            ):
                raise Exception(
                    f"""This fixture created a `{type(result)}.{type(result.app) if getattr(result, "app", None) else "None"}` application, but is only meant for `{Flask}`.
Ensure either that [openapi] is not set in the [flask] config, or use the `openapi_client` fixture."""
                )

            app = result.app
            client = stack.enter_context(app.test_client())

            app = client.application

            flask_session_ctx_manager = cast(
                _GeneratorContextManager[SecureCookieSession],
                client.session_transaction(),
            )
            flask_session = stack.enter_context(flask_session_ctx_manager)
            flask_session["_id"] = get_random_str()
            client.set_cookie(
                cast(str, app.config["SESSION_COOKIE_NAME"]),
                encrypt_flask_cookie(
                    cast(str, app.config["SECRET_KEY"]), flask_session
                ),
                domain="localhost",
                # fmt: off
                max_age=app.config['PERMANENT_SESSION_LIFETIME'] if app.config['PERMANENT_SESSION'] else None,
                # fmt: on
            )

            yield ClientInjector(client, result.flask_injector)

    def _openapi_client(
        self, flask_app_getter: AppGetter[FlaskApp]
    ) -> Generator[OpenAPIClientInjector, Any, None]:
        with ExitStack() as stack:
            result = flask_app_getter()

            if not isinstance(
                result, AppInjector
            ) or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                result.app, FlaskApp
            ):
                raise Exception(
                    f"""This fixture created a `{type(result)}.{type(result.app) if getattr(result, "app", None) else "None"}` application, but is only meant for `{FlaskApp}`.
Ensure either that [openapi] is set in the [flask] config, or use the `flask_client` fixture."""
                )
            app = result.app
            app.add_middleware(
                TrustedHostMiddleware, allowed_hosts=["localhost", "localhost:5000"]
            )
            client = stack.enter_context(app.test_client())
            # TODO OpenAPI requires more work before sessions are working. Flask can use this code, but BL_Python.web doesn't support sessions yet anyway.
            # client.cookies.set(
            #    cast(str, app.config["SESSION_COOKIE_NAME"]),
            #    encrypt_flask_cookie(
            #        cast(str, app.config["SECRET_KEY"]), flask_session
            #    ),
            #    domain="localhost",
            #    # fmt: off
            #    max_age=app.config['PERMANENT_SESSION_LIFETIME'] if app.config['PERMANENT_SESSION'] else None,
            #    # fmt: on
            # )
            #                cast(Flask, client.app.app).wsgi_app = TestSessionMiddleware(
            #                    cast(Flask, client.app.app).wsgi_app
            #                )
            # pass
            # app = cast(Flask, client.app.app)
            yield ClientInjector(client, result.flask_injector)

    @pytest.fixture()
    def flask_client(
        self, _get_basic_flask_app: FlaskAppInjector
    ) -> FlaskClientInjector:
        return next(self._flask_client(lambda: _get_basic_flask_app))

    @pytest.fixture()
    def openapi_client(
        self, _get_openapi_app: AppInjector[FlaskApp]
    ) -> OpenAPIClientInjector:
        return next(self._openapi_client(lambda: _get_openapi_app))

    def _client_configurable(
        self,
        mocker: MockerFixture,
        app_getter: Callable[
            [Config, MockerFixture], Generator[AppInjector[T_app], Any, None]
        ],
        client_getter: Callable[
            [AppGetter[T_app]],
            Generator[ClientInjector[T_flask_client], Any, None],
        ],
    ):
        def _client_getter(
            config: Config, app_init_hook: TAppInitHook[T_app] | None = None
        ):
            application_result = next(app_getter(config, mocker))
            if app_init_hook is not None:
                app_init_hook(application_result)
            return next(client_getter(lambda: application_result))

        return _client_getter

    @pytest.fixture()
    def flask_client_configurable(
        self, mocker: MockerFixture
    ) -> FlaskClientInjectorConfigurable:
        return self._client_configurable(
            mocker, self.__get_basic_flask_app, self._flask_client
        )

    @pytest.fixture()
    def openapi_client_configurable(
        self, mocker: MockerFixture
    ) -> OpenAPIClientInjectorConfigurable:
        return self._client_configurable(
            mocker, self.__get_openapi_app, self._openapi_client
        )

    def _flask_request(
        self,
        flask_client: FlaskClient,
        request_context_args: dict[Any, Any] | None = None,
    ) -> Generator[RequestContext, Any, None]:
        with flask_client.application.test_request_context(
            **(request_context_args or {})
        ) as request_context:
            yield request_context

    def _openapi_request(
        self,
        openapi_client: TestClient,
        request_context_args: dict[Any, Any] | None = None,
    ) -> Generator[RequestContext, Any, None]:
        with cast(FlaskApp, openapi_client.app).app.test_request_context(
            **(request_context_args or {})
        ) as request_context:
            yield request_context

    @pytest.fixture()
    def flask_request(
        self, flask_client: FlaskClient
    ) -> Generator[RequestContext, Any, None]:
        with next(self._flask_request(flask_client)) as request_context:
            yield request_context

    @pytest.fixture()
    def openapi_request(
        self, openapi_client: TestClient
    ) -> Generator[RequestContext, Any, None]:
        with next(self._openapi_request(openapi_client)) as request_context:
            yield request_context

    @pytest.fixture()
    def flask_request_configurable(
        self,
        flask_client_configurable: FlaskClientInjectorConfigurable,
    ) -> RequestConfigurable:
        def _flask_request_getter(
            config: Config, request_context_args: dict[Any, Any] | None = None
        ):
            flask_client = flask_client_configurable(config)
            request_context = next(
                self._flask_request(flask_client.client, request_context_args)
            )
            return request_context

        return _flask_request_getter

    @pytest.fixture()
    def openapi_request_configurable(
        self,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
    ) -> RequestConfigurable:
        def _flask_request_getter(
            config: Config, request_context_args: dict[Any, Any] | None = None
        ):
            flask_client = openapi_client_configurable(config)
            request_context = next(
                self._openapi_request(flask_client.client, request_context_args)
            )
            return request_context

        return _flask_request_getter

    @lru_cache
    def _get_openapi_spec(self):
        return yaml.safe_load(
            """openapi: 3.0.3
servers:
  - url: http://testserver/
    description: Test Application
info:
  title: "Test Application"
  version: 3.0.3
paths:
  /:
    get:
      description: "Check whether the application is running."
      operationId: "root.get"
      parameters: []
      responses:
        "200":
          content:
            application/json:
              schema:
                type: string
          description: "Application is running correctly."
      summary: "A simple method that returns 200 as long as the application is running."
"""
        )

    @pytest.fixture()
    def openapi_mock_controller(self, request: FixtureRequest, mocker: MockerFixture):
        fixture_name = CreateApp.openapi_mock_controller.__name__
        parameter_error_msg = f"The first parameter to the `{fixture_name}` fixture must be a `Callable[[], Response]`. Review the documentation for `OpenAPIMockController`."

        get_handler: Callable[[], Response]
        # TODO probably log when this happens
        if not getattr(request, "param", None):
            get_handler = lambda: Response()
        else:
            get_handler = request.param

        if not callable(get_handler):
            raise Exception(parameter_error_msg)

        openapi_spec_module_name = "root"
        openapi_spec_root_module = ModuleType(openapi_spec_module_name)

        setattr(openapi_spec_root_module, "get", lambda: get_handler())
        sys.modules[openapi_spec_module_name] = openapi_spec_root_module
        openapi_spec_import_module = MagicMock(return_value=openapi_spec_root_module)

        # don't create the app, just prep for
        # the app to load all these mocks instead
        importlib_mock: MockType | None = None
        spec_loader_mock: MockType | None = None

        def begin():
            nonlocal importlib_mock, spec_loader_mock

            if importlib_mock is None:
                importlib_mock = mocker.patch(
                    "connexion.utils.importlib",
                    spec=importlib,
                    import_module=openapi_spec_import_module,
                )

            if spec_loader_mock is None:
                spec_loader_mock = mocker.patch(
                    "connexion.spec.Specification._load_spec_from_file",
                    return_value=self._get_openapi_spec(),
                )

        def end():
            nonlocal importlib_mock, spec_loader_mock

            if importlib_mock is not None:
                mocker.stop(importlib_mock)

            if spec_loader_mock is not None:
                mocker.stop(spec_loader_mock)

        mock_controller = MockController(begin=begin, end=end)

        try:
            yield mock_controller
        finally:
            mock_controller.end()
            _ = sys.modules.pop(openapi_spec_module_name)

    # https://stackoverflow.com/a/55079736
    # creates a fixture on this class called `setup_method_fixture`
    # then tells pytest to use it for every test in the class
    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, mocker: MockerFixture):
        setup_artifacts = self._pre_test_setup(mocker)
        yield
        self._post_test_teardown(setup_artifacts)

    def _pre_test_setup(self, mocker: MockerFixture):
        # the pytest log formatters need to be restored
        # in the event json_logging changes them, otherwise
        # some tests may fail
        log_formatters = [handler.formatter for handler in logging.getLogger().handlers]

        self._automatic_mocks = {}

        mock_targets: list[tuple[str] | tuple[str, Any]] = [
            ("io.open",),
            ("toml.decoder.loads", {}),
            ("BL_Python.web.application._import_blueprint_modules", []),
            ("BL_Python.web.application._get_program_dir", "."),
            ("BL_Python.web.application._get_exec_dir", "."),
        ]

        for mock_target in mock_targets:
            if len(mock_target) == 1:
                (target_name,) = mock_target
                mock = mocker.patch(target_name)
            else:
                (target_name, return_value) = mock_target
                mock = mocker.patch(target_name)
                mock.return_value = return_value

            self._automatic_mocks[target_name] = mock

        return log_formatters

    def _post_test_teardown(self, log_formatters: list[logging.Formatter | None]):
        self._automatic_mocks = {}

        for i, handler in enumerate(logging.getLogger().handlers):
            # this assumes handlers are in the same order
            # so is prone to breakage
            handler.formatter = log_formatters[i]

        # json_logging relies on global, so they must be reset between each test
        _ = importlib.reload(json_logging)
