import importlib
import logging
import sys
from collections import defaultdict
from contextlib import _GeneratorContextManager  # pyright: ignore[reportPrivateUsage]
from contextlib import ExitStack
from dataclasses import dataclass
from types import ModuleType
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    NamedTuple,
    Protocol,
    Sequence,
    TypeVar,
    cast,
)
from unittest.mock import AsyncMock, MagicMock, NonCallableMagicMock

import json_logging
import pytest
from _pytest.fixtures import SubRequest
from connexion import FlaskApp
from flask import Flask, Request, Response, session
from flask.ctx import RequestContext
from flask.sessions import SecureCookieSession
from flask.testing import FlaskClient
from flask_injector import FlaskInjector
from injector import Module
from Ligare.database.migrations.alembic.env import set_up_database
from Ligare.identity.config import SAML2Config, SSOConfig
from Ligare.platform.dependency_injection import UserLoaderModule
from Ligare.platform.identity import Role, User
from Ligare.platform.identity.user_loader import TRole, UserId, UserMixin
from Ligare.programming.collections.dict import NestedDict
from Ligare.programming.config import AbstractConfig, ConfigBuilder
from Ligare.programming.str import get_random_str
from Ligare.web.application import (
    ApplicationBuilder,
    CreateAppResult,
    FlaskAppResult,
    OpenAPIAppResult,
    T_app,
)
from Ligare.web.config import (
    Config,
    FlaskConfig,
    FlaskOpenApiConfig,
    FlaskSessionConfig,
    FlaskSessionCookieConfig,
)
from Ligare.web.encryption import encrypt_flask_cookie
from Ligare.web.middleware.sso import SAML2MiddlewareModule
from mock import MagicMock
from pytest import FixtureRequest
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.testclient import TestClient
from typing_extensions import Self
from werkzeug.local import LocalProxy

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

    def __call__(
        self,
    ) -> CreateAppResult[T_app]: ...


TAppInitHook = (
    Callable[[list[type[AbstractConfig]], list[Module | type[Module]]], None] | None
)
TClientInitHook = Callable[[CreateAppResult[T_app]], None] | None


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
        client_init_hook: TClientInitHook[T_app] | None = None,
        app_init_hook: TAppInitHook | None = None,
    ) -> Generator[ClientInjector[T_flask_client], Any, None]: ...


FlaskClientInjectorConfigurable = ClientInjectorConfigurable[Flask, FlaskClient]
OpenAPIClientInjectorConfigurable = ClientInjectorConfigurable[FlaskApp, TestClient]
FlaskClientInjector = ClientInjector[FlaskClient]
OpenAPIClientInjector = ClientInjector[TestClient]
OpenAPIClientInjectorWithDatabase = tuple[OpenAPIClientInjector, Connection]
OpenAPIClientInitHook = TClientInitHook[FlaskApp]
OpenAPIAppInitHook = TAppInitHook


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
        from flask import request

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


class CreateApp(Generic[T_app]):
    app_name: str = "test_app"
    auto_mock_dependencies: bool = True
    default_app_getter: AppGetter[T_app] | None = None
    use_inmemory_database: bool = True

    _automatic_mocks: dict[str, MagicMock] = defaultdict()

    def _basic_config(self) -> Config:
        config = (
            ConfigBuilder[Config]()
            .with_root_config(Config)
            .with_configs([SSOConfig])
            .build()
        )()
        config.flask = FlaskConfig(
            app_name=self.app_name,
            env="Testing",
            session=FlaskSessionConfig(
                cookie=FlaskSessionCookieConfig(secret_key=get_random_str())
            ),
        )
        return config

    def _openapi_config(self) -> Config:
        config = self._basic_config()
        cast(FlaskConfig, config.flask).openapi = FlaskOpenApiConfig(
            spec_path="openapi.yaml", use_swagger=False
        )
        return config

    @pytest.fixture()
    def basic_config(self):
        return self._basic_config()

    @pytest.fixture()
    def openapi_config(self):
        return self._openapi_config()

    _MOCK_USER_USERNAME = "test user"

    def get_authenticated_request_context(
        self,
        app: ClientInjector[T_flask_client],
        user: type[UserMixin[TRole]],
        mocker: MockerFixture,
        roles: Sequence[TRole] | None = None,
    ):
        _ = self.mock_user(user, mocker, roles)

        with app.injector.app.test_request_context() as request_context:
            session["_id"] = get_random_str()
            session["authenticated"] = True
            session["username"] = CreateApp._MOCK_USER_USERNAME

            app_config = cast(dict[str, Any], app.injector.app.config)

            if isinstance(app.client, TestClient):
                session_cookie = encrypt_flask_cookie(
                    # TODO use app.client.injector?
                    app_config["SECRET_KEY"],
                    {
                        "_id": session["_id"],
                        "authenticated": True,
                        "username": CreateApp._MOCK_USER_USERNAME,
                    },
                )

                app.client.cookies.set(
                    app_config["SESSION_COOKIE_NAME"], session_cookie
                )
            else:
                # TODO move the session_transaction stuff from the Flask test client stuff here.
                raise NotImplementedError(
                    f"Authenticated request context for `{FlaskClient.__name__}` not implemented."
                )

            return request_context

    def mock_user(
        self,
        user: type[UserMixin[TRole]],
        mocker: MockerFixture,
        roles: Sequence[TRole] | None = None,
    ) -> MagicMock | AsyncMock | NonCallableMagicMock:
        if roles is None:
            roles = cast(Sequence[TRole], ())

        def get_mock_user(proxy: LocalProxy[UserMixin[TRole]] | None = None):
            if proxy is not None:
                return proxy
            user_id = UserId(1, CreateApp._MOCK_USER_USERNAME)
            # FIXME this needs to handle user roles
            return user(user_id, roles)

        return mocker.patch("flask_login.utils._get_user", side_effect=get_mock_user)

    def _client_configurable(
        self,
        mocker: MockerFixture,
        app_getter: Callable[
            [Config, MockerFixture, TAppInitHook | None],
            Generator[CreateAppResult[T_app], Any, None],
        ],
        client_getter: Callable[
            [AppGetter[T_app]],
            Generator[ClientInjector[T_flask_client], Any, None],
        ],
    ) -> ClientInjectorConfigurable[T_app, T_flask_client]:
        def _client_getter(
            config: Config,
            client_init_hook: TClientInitHook[T_app] | None = None,
            app_init_hook: TAppInitHook | None = None,
        ) -> Generator[ClientInjector[T_flask_client], Any, None]:
            application_result = next(app_getter(config, mocker, app_init_hook))

            if client_init_hook is not None:
                client_init_hook(application_result)

            app_result = next(client_getter(lambda: application_result))
            with app_result.injector.app.app_context():
                yield app_result

        return _client_getter

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
            ("Ligare.web.application._import_blueprint_modules", []),
            ("Ligare.web.application._get_program_dir", "."),
            ("Ligare.web.application._get_exec_dir", ".."),
        ]

        if self.auto_mock_dependencies:
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


class CreateFlaskApp(CreateApp[Flask]):
    def __get_basic_flask_app(
        self,
        config: Config,
        mocker: MockerFixture,
        app_init_hook: TAppInitHook | None = None,
    ) -> Generator[FlaskAppResult, Any, None]:
        # prevents the creation of a Connexion application
        if config.flask is not None:
            config.flask.openapi = None
            config.sso = SSOConfig(  # pyright: ignore[reportAttributeAccessIssue]
                protocol="SAML2",
                settings=SAML2Config(relay_state="", metadata_url="", metadata=""),
            )

        _ = mocker.patch("Ligare.web.application.load_config", return_value=config)
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=config)),
        )

        application_configs: list[type[AbstractConfig]] | None = []
        application_modules: list[Module | type[Module]] | None = []

        if app_init_hook is not None:
            app_init_hook(application_configs, application_modules)

        application_modules.append(SAML2MiddlewareModule)

        logging.basicConfig(force=True)

        application_builder = (
            ApplicationBuilder[Flask]()
            .with_modules(application_modules)
            .use_configuration(
                lambda config_builder: config_builder.enable_ssm(True)
                .with_config_filename("config.toml")
                .with_root_config_type(Config)
                .with_config_types(application_configs)
            )
        )
        app = application_builder.build()
        yield app

    @pytest.fixture()
    def _get_basic_flask_app(
        self, basic_config: Config, mocker: MockerFixture
    ) -> FlaskAppResult:
        return next(self.__get_basic_flask_app(basic_config, mocker))

    def _flask_client(
        self, flask_app_getter: AppGetter[Flask]
    ) -> Generator[FlaskClientInjector, Any, None]:
        with ExitStack() as stack:
            result = flask_app_getter()

            if not isinstance(result, CreateAppResult) or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                result.app_injector.app, Flask
            ):
                raise Exception(
                    f"""This fixture created a `{type(result)}.{type(result.app_injector.app) if getattr(result, "app", None) else "None"}` application, but is only meant for `{Flask}`.
Ensure either that [openapi] is not set in the [flask] config, or use the `openapi_client` fixture."""
                )

            app = result.app_injector.app
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
                max_age=app.config["PERMANENT_SESSION_LIFETIME"]
                if app.config["PERMANENT_SESSION"]
                else None,
                # fmt: on
            )

            yield ClientInjector(client, result.app_injector.flask_injector)

    @pytest.fixture()
    def flask_client(self, _get_basic_flask_app: FlaskAppResult) -> FlaskClientInjector:
        return next(self._flask_client(lambda: _get_basic_flask_app))

    @pytest.fixture()
    def flask_client_configurable(
        self, mocker: MockerFixture
    ) -> FlaskClientInjectorConfigurable:
        return self._client_configurable(
            mocker, self.__get_basic_flask_app, self._flask_client
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

    @pytest.fixture()
    def flask_request(
        self, flask_client: FlaskClient
    ) -> Generator[RequestContext, Any, None]:
        with next(self._flask_request(flask_client)) as request_context:
            yield request_context

    @pytest.fixture()
    def flask_request_configurable(
        self,
        flask_client_configurable: FlaskClientInjectorConfigurable,
    ) -> RequestConfigurable:
        def _flask_request_getter(
            config: Config, request_context_args: dict[Any, Any] | None = None
        ):
            flask_client = next(flask_client_configurable(config))
            request_context = next(
                self._flask_request(flask_client.client, request_context_args)
            )
            return request_context

        return _flask_request_getter


class CreateOpenAPIApp(CreateApp[FlaskApp]):
    def _get_real_openapi_app(
        self,
        config: Config,
        mocker: MockerFixture,
        app_init_hook: TAppInitHook | None = None,
    ) -> Generator[OpenAPIAppResult, Any, None]:
        # prevents the creation of a Connexion application
        if config.flask is None or config.flask.openapi is None:
            raise Exception(
                "[openapi] not set in config. Cannot create OpenAPI test client."
            )

        _ = mocker.patch("Ligare.web.application.load_config", return_value=config)
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=config)),
        )

        _application_configs: list[type[AbstractConfig]] = []
        _application_modules = cast(
            list[Module | type[Module]],
            [
                SAML2MiddlewareModule,
                UserLoaderModule(
                    loader=User,  # pyright: ignore[reportArgumentType]
                    roles=Role,  # pyright: ignore[reportArgumentType]
                    user_table=MagicMock(),  # pyright: ignore[reportArgumentType]
                    role_table=MagicMock(),  # pyright: ignore[reportArgumentType]
                    bases=[],
                ),
            ],
        )

        if app_init_hook is not None:
            app_init_hook(_application_configs, _application_modules)

        application_builder = (
            ApplicationBuilder[FlaskApp]()
            .with_modules(_application_modules)
            .use_configuration(
                lambda config_builder: config_builder.enable_ssm(True)
                .with_config_filename("config.toml")
                .with_root_config_type(Config)
                .with_config_types(_application_configs)
            )
        )
        app = application_builder.build()
        yield app

    @pytest.fixture()
    def _get_openapi_app(
        self,
        openapi_config: Config,
        mocker: MockerFixture,
        openapi_mock_controller: OpenAPIMockController,
    ) -> OpenAPIAppResult:
        _ = mocker.patch("Ligare.web.application.json_logging")
        openapi_mock_controller.begin()
        return next(self._get_real_openapi_app(openapi_config, mocker))

    def _openapi_client(
        self, flask_app_getter: AppGetter[FlaskApp]
    ) -> Generator[OpenAPIClientInjector, Any, None]:
        with ExitStack() as stack:
            result = flask_app_getter()

            if not isinstance(result, CreateAppResult) or not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
                result.app_injector.app, FlaskApp
            ):
                raise Exception(
                    f"""This fixture created a `{type(result)}.{type(result.app_injector.app) if getattr(result, "app", None) else "None"}` application, but is only meant for `{FlaskApp}`.
Ensure either that [openapi] is set in the [flask] config, or use the `flask_client` fixture."""
                )
            config = result.app_injector.flask_injector.injector.get(Config)
            host = config.flask.host if config.flask else "localhost"
            port = config.flask.port if config.flask else "5000"
            result.app_injector.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=[host, f"{host}:{port}"],
            )

            client: TestClient = stack.enter_context(
                result.app_injector.app.test_client()
            )

            app_config = cast(dict[str, Any], result.app_injector.app.app.config)

            _ = client.headers.setdefault("Host", app_config["SERVER_NAME"])

            yield ClientInjector(client, result.app_injector.flask_injector)

    # TODO this needs to support plain old Flask at some point
    def get_app(self, flask_app_getter: AppGetter[FlaskApp]):
        return next(self._openapi_client(flask_app_getter))

    @pytest.fixture()
    def openapi_client_with_database(
        self, request: SubRequest
    ) -> Generator[tuple[OpenAPIClientInjector, Connection], Any, None]:
        if self.use_inmemory_database:
            _ = request.getfixturevalue("use_inmemory_database")

        openapi_client = request.getfixturevalue("openapi_client")

        with openapi_client.injector.injector.get(Session) as session:
            # Get a connection to share so Alembic does not wipe out the in-memory database
            # when using SQLite in-memory connections
            if session.bind is None:
                raise Exception(
                    "SQLAlchemy Session is not bound to an engine. This is not supported."
                )

            with set_up_database(session.bind.engine) as connection:
                yield (openapi_client, connection)

    @pytest.fixture()
    def openapi_client(
        self,
        request: SubRequest,
    ) -> OpenAPIClientInjector:
        # Call `default_app_getter` as a class method because:
        # 1. A method assigned as a value to a class member becomes a class
        #    member itself which means `self` is implicitly passed to the method
        # 2. `AppGetter[T_app]` does not take parameters, and the implicit `self`
        #    causes a runtime call error.
        # 3. The only way to avoid the class member behavior is to avoid
        #    assigning the class member value (during declaration), instead
        #    assigning it as an object value (during instantiation or later).
        # 4. Pytest does not load tests in a class that has an __init__ method
        #    so we cannot use a ctor to assign the value
        #
        # also:
        # assertions in self._openapi_client check the actual type,
        # so this cast is just to appease pyright.
        # TODO support this for Flask as well
        default_app_getter = cast(Self, self.__class__).default_app_getter

        get_openapi_app: CreateAppResult[FlaskApp]
        if default_app_getter is None:
            get_openapi_app = request.getfixturevalue("_get_openapi_app")
        else:
            get_openapi_app = default_app_getter()

        return next(self._openapi_client(lambda: get_openapi_app))

    @pytest.fixture()
    def openapi_client_configurable(
        self, mocker: MockerFixture
    ) -> OpenAPIClientInjectorConfigurable:
        # FIXME some day json_logging needs to be fixed
        _ = mocker.patch("Ligare.web.application.json_logging")
        return self._client_configurable(
            mocker, self._get_real_openapi_app, self._openapi_client
        )

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
    def openapi_request(
        self, openapi_client: TestClient
    ) -> Generator[RequestContext, Any, None]:
        with next(self._openapi_request(openapi_client)) as request_context:
            yield request_context

    @pytest.fixture()
    def openapi_request_configurable(
        self,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
    ) -> RequestConfigurable:
        def _flask_request_getter(
            config: Config, request_context_args: dict[Any, Any] | None = None
        ):
            flask_client = next(openapi_client_configurable(config))
            request_context = next(
                self._openapi_request(flask_client.client, request_context_args)
            )
            return request_context

        return _flask_request_getter

    # this is the YAML-parsed dictionary from this OpenAPI spec
    # openapi: 3.0.3
    # servers:
    # - url: http://testserver/
    #    description: Test Application
    # info:
    # title: "Test Application"
    # version: 3.0.3
    # paths:
    # /:
    #    get:
    #    description: "Check whether the application is running."
    #    operationId: "root.get"
    #    parameters: []
    #    responses:
    #        "200":
    #        content:
    #            application/json:
    #            schema:
    #                type: string
    #        description: "Application is running correctly."
    #    summary: "A simple method that returns 200 as long as the application is running."
    _openapi_spec: NestedDict[str, Any] = {
        "info": {"title": "Test Application", "version": "3.0.3"},
        "openapi": "3.0.3",
        "paths": {
            "/": {
                "get": {
                    "description": "Check whether the application is running.",
                    "operationId": "root.get",
                    "parameters": [],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"schema": {"type": "string"}}
                            },
                            "description": "Application is running correctly",
                        }
                    },
                    "summary": "A simple method that returns 200 as long as the application is running.",
                }
            }
        },
        "servers": [{"description": "Test Application", "url": "http://testserver/"}],
    }

    @pytest.fixture()
    def openapi_mock_controller(self, request: FixtureRequest, mocker: MockerFixture):
        fixture_name = CreateOpenAPIApp.openapi_mock_controller.__name__
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
                    return_value=CreateOpenAPIApp._openapi_spec,
                )

        def end():
            nonlocal importlib_mock, spec_loader_mock

            if importlib_mock is not None:
                mocker.stop(importlib_mock)

            if spec_loader_mock is not None:
                mocker.stop(spec_loader_mock)

        mock_controller = MockController(begin=begin, end=end)

        try:
            # TODO can this be a context manager instead of requiring
            # the explicit begin() call?
            yield mock_controller
        finally:
            mock_controller.end()
            _ = sys.modules.pop(openapi_spec_module_name)
