from os import environ

import pytest
from connexion import FlaskApp
from flask import Flask
from Ligare.programming.config import AbstractConfig
from Ligare.programming.str import get_random_str
from Ligare.web.application import App  # pyright:ignore[reportDeprecated]
from Ligare.web.application import ApplicationBuilder, configure_openapi
from Ligare.web.config import Config, FlaskConfig, FlaskOpenApiConfig
from Ligare.web.testing.create_app import CreateOpenAPIApp
from mock import MagicMock
from pydantic import BaseModel
from pytest_mock import MockerFixture
from typing_extensions import override


class TestCreateOpenAPIApp(CreateOpenAPIApp):
    def test__CreateOpenAPIApp__configure_openapi__requires_flask_config(self):
        with pytest.raises(
            Exception,
            match=r"^OpenAPI configuration is empty\. Review the `openapi` section of your application's `config\.toml`\.$",
        ):
            _ = configure_openapi(Config())

    def test__CreateOpenAPIApp__configure_openapi__creates_flask_app_using_config(
        self, mocker: MockerFixture
    ):
        _ = mocker.patch("Ligare.web.application.json_logging")
        connexion_mock = mocker.patch("Ligare.web.application.FlaskApp")

        app_name = f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__configure_openapi__creates_flask_app_using_config.__name__}-app_name"
        spec_path = ".."

        _ = configure_openapi(
            Config(
                flask=FlaskConfig(
                    app_name=app_name,
                    openapi=FlaskOpenApiConfig(spec_path=spec_path),
                )
            )
        )

        connexion_mock.assert_called_with(app_name, specification_dir=spec_path)

    def test__CreateOpenAPIApp__create_app__loads_config_from_toml(
        self, basic_config: Config, mocker: MockerFixture
    ):
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        load_config_mock = mocker.patch(
            "Ligare.web.application.load_config", return_value=basic_config
        )

        toml_filename = f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__create_app__loads_config_from_toml.__name__}-config.toml"
        application_builder = ApplicationBuilder[Flask]().use_configuration(
            lambda config_builder: config_builder.with_config_filename(toml_filename)
        )
        _ = application_builder.build()
        assert load_config_mock.called
        assert load_config_mock.call_args and load_config_mock.call_args[0]
        assert load_config_mock.call_args[0][1] == toml_filename

    def test__CreateOpenAPIApp__create_app__uses_custom_config_types(
        self, mocker: MockerFixture
    ):
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        toml_filename = f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__create_app__uses_custom_config_types.__name__}-config.toml"
        toml_load_result = {
            "flask": {
                "app_name": f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__create_app__uses_custom_config_types.__name__}-app_name"
            },
            "custom": {"foo": get_random_str(k=26)},
        }

        _ = mocker.patch("toml.load", return_value=toml_load_result)

        class CustomConfig(BaseModel, AbstractConfig):
            @override
            def post_load(self) -> None:
                return super().post_load()

            foo: str = get_random_str(k=26)

        app = App[Flask].create(  # pyright:ignore[reportDeprecated]
            config_filename=toml_filename, application_configs=[CustomConfig]
        )

        assert (
            app.app_injector.flask_injector.injector.get(CustomConfig).foo
            == toml_load_result["custom"]["foo"]
        )

    @pytest.mark.parametrize(
        "envvar_name,config_var_name,var_value",
        [
            ("FLASK_APP", "app_name", "foobar"),
            ("FLASK_ENV", "env", "barfoo"),
        ],
    )
    def test__CreateOpenAPIApp__create_app__updates_flask_config_from_envvars(
        self,
        envvar_name: str,
        config_var_name: str,
        var_value: str,
        basic_config: Config,
        mocker: MockerFixture,
    ):
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        object.__setattr__(basic_config.flask, config_var_name, var_value)

        environ.update({envvar_name: var_value})
        _ = mocker.patch(
            "Ligare.web.application.load_config", return_value=basic_config
        )
        _ = App[Flask].create()  # pyright:ignore[reportDeprecated]

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
    def test__CreateOpenAPIApp__create_app__requires_application_name(
        self,
        envvar_name: str | None,
        config_var_name: str | None,
        var_value: str,
        should_fail: bool,
        mocker: MockerFixture,
    ):
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        environ.update({"FLASK_APP": "", "FLASK_ENV": ""})

        if envvar_name is not None:
            environ.update({envvar_name: var_value})

        toml_load_result = {}
        if config_var_name is not None:
            toml_load_result["flask"] = {config_var_name: var_value}

        _ = mocker.patch("toml.load", return_value=toml_load_result)

        if should_fail:
            with pytest.raises(Exception):
                _ = App[Flask].create()  # pyright:ignore[reportDeprecated]
        else:
            _ = App[Flask].create()  # pyright:ignore[reportDeprecated]

    def test__CreateOpenAPIApp__create_app__configures_appropriate_app_type_based_on_config(
        self, mocker: MockerFixture
    ):
        toml_filename = f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__create_app__configures_appropriate_app_type_based_on_config.__name__}-config.toml"
        app_name = f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__create_app__configures_appropriate_app_type_based_on_config.__name__}-app_name"
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        _ = mocker.patch("Ligare.web.application.register_error_handlers")
        _ = mocker.patch("Ligare.web.application.register_api_request_handlers")
        _ = mocker.patch("Ligare.web.application.register_api_response_handlers")
        _ = mocker.patch("Ligare.web.application.configure_dependencies")

        configure_method_mock = mocker.patch("Ligare.web.application.configure_openapi")
        config = Config(
            flask=FlaskConfig(app_name=app_name, openapi=FlaskOpenApiConfig())
        )
        _ = mocker.patch("Ligare.web.application.load_config", return_value=config)
        _ = App[FlaskApp].create(config_filename=toml_filename)  # pyright:ignore[reportDeprecated]

        configure_method_mock.assert_called_once_with(config)
