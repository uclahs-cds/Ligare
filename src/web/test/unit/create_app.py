from contextlib import _GeneratorContextManager  # pyright: ignore[reportPrivateUsage]
from contextlib import ExitStack
from typing import Any, Generator, Protocol, cast

import json_logging
import pytest
from BL_Python.programming.str import get_random_str
from BL_Python.web.application import create_app
from BL_Python.web.config import (
    Config,
    FlaskConfig,
    FlaskSessionConfig,
    FlaskSessionCookieConfig,
)
from BL_Python.web.encryption import encrypt_flask_cookie
from flask import Flask
from flask.ctx import RequestContext
from flask.sessions import SecureCookieSession
from flask.testing import FlaskClient
from pytest_mock import MockerFixture


class FlaskAppGetter(Protocol):
    def __call__(self) -> Flask:
        ...


class FlaskClientConfigurable(Protocol):
    def __call__(self, config: Config) -> FlaskClient:
        ...


class FlaskRequestConfigurable(Protocol):
    def __call__(
        self, config: Config, request_context_args: dict[Any, Any] | None = None
    ) -> RequestContext:
        ...


class CreateApp:
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
    ) -> Generator[Flask, Any, None]:
        with mocker.patch(
            "BL_Python.web.application.load_config",
            return_value=config,
        ):
            app = create_app()
            yield app

    @pytest.fixture()
    def _get_basic_flask_app(
        self, basic_config: Config, mocker: MockerFixture
    ) -> Flask:
        return next(self.__get_basic_flask_app(basic_config, mocker))

    def _flask_client(
        self, flask_app_getter: FlaskAppGetter
    ) -> Generator[FlaskClient, Any, None]:
        with ExitStack() as stack:
            client = stack.enter_context(flask_app_getter().test_client())
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
            yield client

    @pytest.fixture()
    def flask_client(self, _get_basic_flask_app: Flask) -> FlaskClient:
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
                self._flask_request(flask_client, request_context_args)
            )
            return request_context

        return _flask_request_getter

    # https://stackoverflow.com/a/55079736
    # creates a fixture on this class called `setup_method_fixture`
    # then tells pytest to use it for every test in the class
    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, mocker: MockerFixture):
        _ = mocker.patch("io.open")
        _ = mocker.patch("toml.decoder.loads", return_value={})
        _ = mocker.patch(
            "BL_Python.web.application._import_blueprint_modules", return_value=[]
        )
        # json_logging relies on global, so they must be reset between each test
        json_logging._current_framework = None  # pyright: ignore[reportPrivateUsage]
        json_logging._request_util = None  # pyright: ignore[reportPrivateUsage]
        json_logging._default_formatter = None  # pyright: ignore[reportPrivateUsage]
        json_logging.ENABLE_JSON_LOGGING = False
        json_logging.ENABLE_JSON_LOGGING_DEBUG = False
