import importlib
import logging
from collections import defaultdict
from contextlib import _GeneratorContextManager  # pyright: ignore[reportPrivateUsage]
from contextlib import ExitStack
from functools import lru_cache
from typing import Any, Generator, NamedTuple, Protocol, cast

import json_logging
import pytest
import yaml
from BL_Python.programming.str import get_random_str
from BL_Python.web.application import FlaskAppInjector, create_app
from BL_Python.web.config import (
    Config,
    FlaskConfig,
    FlaskSessionConfig,
    FlaskSessionCookieConfig,
)
from BL_Python.web.encryption import encrypt_flask_cookie
from connexion import (  # pyright: ignore[reportMissingTypeStubs] Connexion is missing py.typed file
    FlaskApp,
)
from flask.ctx import RequestContext
from flask.sessions import SecureCookieSession
from flask.testing import FlaskClient
from flask_injector import FlaskInjector
from mock import MagicMock
from pytest_mock import MockerFixture


class FlaskClientInjector(NamedTuple):
    client: FlaskClient
    injector: FlaskInjector
    connexion_app: FlaskApp | None = None


class FlaskAppGetter(Protocol):
    def __call__(self) -> FlaskAppInjector:
        ...


class FlaskClientConfigurable(Protocol):
    def __call__(self, config: Config) -> FlaskClientInjector:
        ...


class FlaskRequestConfigurable(Protocol):
    def __call__(
        self, config: Config, request_context_args: dict[Any, Any] | None = None
    ) -> RequestContext:
        ...


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

    @pytest.fixture()
    def basic_config(self):
        return self._basic_config()

    def __get_basic_flask_app(
        self, config: Config, mocker: MockerFixture
    ) -> Generator[FlaskAppInjector, Any, None]:
        with mocker.patch(
            "BL_Python.web.application.load_config",
            return_value=config,
        ):
            app = create_app()
            yield app

    @pytest.fixture()
    def _get_basic_flask_app(
        self, basic_config: Config, mocker: MockerFixture
    ) -> FlaskAppInjector:
        return next(self.__get_basic_flask_app(basic_config, mocker))

    def _flask_client(
        self, flask_app_getter: FlaskAppGetter
    ) -> Generator[FlaskClientInjector, Any, None]:
        with ExitStack() as stack:
            (app, injector, connexion_app) = flask_app_getter()
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
            yield FlaskClientInjector(client, injector, connexion_app)

    @pytest.fixture()
    def flask_client(
        self, _get_basic_flask_app: FlaskAppInjector
    ) -> FlaskClientInjector:
        return next(self._flask_client(lambda: _get_basic_flask_app))

    @pytest.fixture()
    def flask_client_configurable(
        self, mocker: MockerFixture
    ) -> FlaskClientConfigurable:
        def _flask_client_getter(config: Config):
            return next(
                self._flask_client(
                    lambda: next(self.__get_basic_flask_app(config, mocker))
                )
            )

        return _flask_client_getter

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
        flask_client_configurable: FlaskClientConfigurable,
    ) -> FlaskRequestConfigurable:
        def _flask_request_getter(
            config: Config, request_context_args: dict[Any, Any] | None = None
        ):
            flask_client = flask_client_configurable(config)
            request_context = next(
                self._flask_request(flask_client[0], request_context_args)
            )
            return request_context

        return _flask_request_getter

    x = 0

    @lru_cache
    def _get_openapi_spec(self):
        if self.x > 0:
            raise Exception("FAILURE")
        self.x = 1
        return yaml.safe_load(
            """openapi: 3.0.3
servers:
  - url: http://localhost:5000/
    description: Test Application
info:
  title: "Test Application"
  version: 3.0.3
paths:
  /:
    get:
      description: "Check whether the application is running."
      operationId: "root"
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
            (
                "connexion.spec.Specification._load_spec_from_file",
                self._get_openapi_spec(),
            ),
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
