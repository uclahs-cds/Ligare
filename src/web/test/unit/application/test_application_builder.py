import pathlib
from pathlib import Path
from typing import cast

import pytest
from flask import Blueprint, Flask
from flask.testing import FlaskClient
from Ligare.programming.config.exceptions import ConfigInvalidError
from Ligare.web.application import configure_blueprint_routes
from Ligare.web.config import Config, FlaskConfig
from Ligare.web.middleware.dependency_injection import configure_dependencies
from Ligare.web.testing.create_app import (
    ClientInjector,
    CreateFlaskApp,
    FlaskClientInjectorConfigurable,
)
from mock import MagicMock
from pytest_mock import MockerFixture


class Foo(CreateFlaskApp):
    def test__ApplicationBuilder__configure_dependencies__registers_correct_Flask_instance_with_AppModule(
        self, mocker: MockerFixture, flask_client: ClientInjector[FlaskClient]
    ):
        app_name = f"{Foo.test__ApplicationBuilder__configure_dependencies__registers_correct_Flask_instance_with_AppModule.__name__}-app_name"
        # flask_mock = mocker.patch(
        #    "Ligare.web.application.Flask", spec=Flask, config=MagicMock(),
        # )

        flask_injector = configure_dependencies(flask_client.client.application)

        x = flask_injector.injector.get(Flask)
        assert x == flask_client.client.application
