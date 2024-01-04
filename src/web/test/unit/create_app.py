from contextlib import _GeneratorContextManager  # pyright: ignore[reportPrivateUsage]
from contextlib import ExitStack
from typing import Any, Generator, cast

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
from flask.sessions import SecureCookieSession
from flask.testing import FlaskClient
from pytest_mock import MockerFixture


class CreateApp:
    def _get_basic_config(self):
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
    def _get_basic_flask_app(
        self, mocker: MockerFixture
    ) -> Generator[Flask, Any, None]:
        config = self._get_basic_config()

        with mocker.patch(
            "BL_Python.web.application.load_config",
            return_value=config,
        ):
            app = create_app()
            yield app

    @pytest.fixture()
    def flask_client(
        self, _get_basic_flask_app: Flask
    ) -> Generator[FlaskClient, Any, None]:
        with ExitStack() as stack:
            client = stack.enter_context(_get_basic_flask_app.test_client())
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
    def flask_request(self, flask_client: FlaskClient):
        with flask_client.application.test_request_context() as request_context:
            yield request_context

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
        # json_logging appears not to be threadsafe
        _ = mocker.patch("json_logging.init_flask")
        _ = mocker.patch("json_logging.init_connexion")
        _ = mocker.patch("json_logging.init_request_instrument")
