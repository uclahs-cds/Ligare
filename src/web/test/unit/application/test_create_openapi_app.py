import pytest
from flask import Flask
from Ligare.web.application import ApplicationBuilder, configure_openapi
from Ligare.web.config import Config, FlaskConfig, FlaskOpenApiConfig
from Ligare.web.testing.create_app import CreateOpenAPIApp
from mock import MagicMock
from pytest_mock import MockerFixture


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

        connexion_mock.assert_called()
        assert connexion_mock.call_args.kwargs
        assert connexion_mock.call_args.kwargs["specification_dir"] == spec_path

    def test__CreateOpenAPIApp__create_app__loads_config_from_toml(
        self, basic_config: Config, mocker: MockerFixture
    ):
        _ = mocker.patch(
            "Ligare.AWS.ssm.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        load_config_mock = mocker.patch(
            "Ligare.programming.application.load_config", return_value=basic_config
        )

        toml_filename = f"{TestCreateOpenAPIApp.test__CreateOpenAPIApp__create_app__loads_config_from_toml.__name__}-config.toml"
        application_builder = ApplicationBuilder(Flask).use_configuration(
            lambda config_builder: config_builder.with_config_filename(toml_filename)
        )
        _ = application_builder.build()
        assert load_config_mock.called
        assert load_config_mock.call_args and load_config_mock.call_args[0]
        assert load_config_mock.call_args[0][1] == toml_filename
