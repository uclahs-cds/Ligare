from os import environ
from typing import Any, cast

import pytest
from BL_Python.programming.config import AbstractConfig
from BL_Python.programming.str import get_random_str
from BL_Python.web.application import (
    configure_blueprint_routes,
    configure_openapi,
    create_app,
)
from BL_Python.web.config import Config
from flask_injector import FlaskInjector
from pydantic import BaseModel
from pytest_mock import MockerFixture

from ..create_app import CreateApp, FlaskClientConfigurable


class TestCreateApp(CreateApp):
    def test__create_app__requires_flask_config(
        self, flask_client_configurable: FlaskClientConfigurable
    ):
        with pytest.raises(
            Exception,
            match=r"^You must set \[flask\] in the application configuration\.$",
        ):
            _ = flask_client_configurable(Config())

    # TODO extend blueprint and openapi tests to cover each relevant config attribute
    def test__configure_blueprint_routes__requires_flask_config(self):
        with pytest.raises(
            Exception,
            match=r"^Flask configuration is empty\. Review the `flask` section of your application's `config\.toml`\.$",
        ):
            _ = configure_blueprint_routes(Config())

    def test__configure_openapi__requires_flask_config(self):
        with pytest.raises(
            Exception,
            match=r"^OpenAPI configuration is empty\. Review the `openapi` section of your application's `config\.toml`\.$",
        ):
            _ = configure_openapi(Config())

    def test__create_app__loads_config_from_toml(
        self, basic_config: Config, mocker: MockerFixture
    ):
        load_config_mock = mocker.patch(
            "BL_Python.web.application.load_config", return_value=basic_config
        )

        toml_filename = f"{TestCreateApp.test__create_app__loads_config_from_toml.__name__}-config.toml"
        _ = create_app(config_filename=toml_filename)
        assert load_config_mock.called
        assert load_config_mock.call_args and load_config_mock.call_args[0]
        assert load_config_mock.call_args[0][1] == toml_filename

    def test__create_app__uses_custom_config_types(self, mocker: MockerFixture):
        toml_filename = f"{TestCreateApp.test__create_app__uses_custom_config_types.__name__}-config.toml"
        toml_load_result = {
            "flask": {
                "app_name": f"{TestCreateApp.test__create_app__uses_custom_config_types.__name__}-app_name"
            },
            "custom": {"foo": get_random_str(k=26)},
        }

        _ = mocker.patch("toml.load", return_value=toml_load_result)

        class CustomConfig(BaseModel, AbstractConfig):
            foo: str = get_random_str(k=26)

        app = create_app(
            config_filename=toml_filename, application_configs=[CustomConfig]
        )
        assert (
            cast(FlaskInjector, cast(Any, app).injector).injector.get(CustomConfig).foo
        ) == toml_load_result["custom"]["foo"]

    @pytest.mark.parametrize(
        "envvar_name,config_var_name,var_value",
        [
            ("FLASK_APP", "app_name", "foobar"),
            ("FLASK_ENV", "env", "barfoo"),
        ],
    )
    def test__create_app__updates_flask_config_from_envvars(
        self,
        envvar_name: str,
        config_var_name: str,
        var_value: str,
        basic_config: Config,
        mocker: MockerFixture,
    ):
        object.__setattr__(basic_config.flask, config_var_name, var_value)

        environ.update({envvar_name: var_value})
        _ = mocker.patch(
            "BL_Python.web.application.load_config", return_value=basic_config
        )
        _ = create_app()

        assert object.__getattribute__(basic_config.flask, config_var_name) == var_value

    @pytest.mark.parametrize(
        "envvar_name,config_var_name,var_value,should_fail",
        [
            ("FLASK_APP", None, "foobar", False),
            ("FLASK_ENV", None, "barfoo", False),
            (None, "app_name", "foobar", False),
            (None, "app_name", "", True),
            (None, "env", "barfoo", False),
        ],
    )
    def test__create_app__requires_application_name(
        self,
        envvar_name: str | None,
        config_var_name: str | None,
        var_value: str,
        should_fail: bool,
        mocker: MockerFixture,
    ):
        environ.update({"FLASK_APP": "", "FLASK_ENV": ""})

        if envvar_name is not None:
            environ.update({envvar_name: var_value})

        toml_load_result = {}
        if config_var_name is not None:
            toml_load_result["flask"] = {config_var_name: var_value}

        _ = mocker.patch("toml.load", return_value=toml_load_result)

        if should_fail:
            with pytest.raises(Exception):
                _ = create_app()
        else:
            _ = create_app()
