from typing import Any

import pytest
from flask import Flask
from Ligare.programming.collections.dict import AnyDict
from Ligare.programming.config import AbstractConfig, ConfigBuilder, load_config
from Ligare.programming.config.exceptions import ConfigBuilderStateError
from Ligare.web.application import ApplicationBuilder, ApplicationConfigBuilder
from Ligare.web.config import Config
from Ligare.web.exception import BuilderBuildError, InvalidBuilderStateError
from mock import MagicMock
from pydantic import BaseModel
from pytest_mock import MockerFixture
from typing_extensions import override


def test__Config__load_config__reads_toml_file(mocker: MockerFixture):
    fake_config_dict = {}
    toml_mock = mocker.patch("toml.load", return_value=fake_config_dict)
    _ = load_config(Config, "foo.toml")
    assert toml_mock.called


def test__Config__load_config__initializes_logging_config(mocker: MockerFixture):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config(Config, "foo.toml")
    assert config.logging.log_level == "DEBUG"


def test__Config__load_config__initializes_flask_config(mocker: MockerFixture):
    fake_config_dict = {"flask": {"app_name": "test_app"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config(Config, "foo.toml")
    assert config.flask is not None
    assert config.flask.app_name == "test_app"


def test__Config__prepare_env_for_flask__requires_flask_secret_key_when_sessions_are_used(
    mocker: MockerFixture,
):
    fake_config_dict: AnyDict = {
        "flask": {"app_name": "test_app", "session": {"cookie": {}}}
    }
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    with pytest.raises(
        Exception, match=r"^`flask.session.cookie.secret_key` must be set in config.$"
    ):
        config = load_config(Config, "foo.toml")


@pytest.mark.parametrize("mode", ["ssm", "filename"])
def test__ApplicationConfigBuilder__build__succeeds_with_either_ssm_or_filename(
    mode: str, mocker: MockerFixture
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    _ = mocker.patch("Ligare.AWS.ssm.SSMParameters.load_config")

    def use_configuration(
        config_builder: ConfigBuilder[Config], config_overrides: dict[str, Any]
    ) -> None:
        _ = config_builder.with_root_config(Config)

    application_config_builder = ApplicationConfigBuilder[Config]().use_configuration(
        use_configuration
    )

    if mode == "ssm":
        _ = application_config_builder.use_ssm(True)
    else:
        _ = application_config_builder.use_filename("foo.toml")

    _ = application_config_builder.build()


def test__ApplicationConfigBuilder__build__raises_InvalidBuilderStateError_without_ssm_or_filename(
    mocker: MockerFixture,
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    _ = mocker.patch("Ligare.AWS.ssm.SSMParameters.load_config")

    application_config_builder = ApplicationConfigBuilder[Config]()

    with pytest.raises(InvalidBuilderStateError):
        _ = application_config_builder.build()


def test__ApplicationConfigBuilder__build__raises_BuilderBuildError_when_ssm_fails_and_filename_not_configured(
    mocker: MockerFixture,
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    _ = mocker.patch(
        "Ligare.AWS.ssm.SSMParameters.load_config",
        side_effect=Exception("Test mode failure."),
    )

    application_config_builder = ApplicationConfigBuilder[Config]().use_ssm(True)

    with pytest.raises(BuilderBuildError):
        _ = application_config_builder.build()


def test__ApplicationConfigBuilder__build__uses_filename_when_ssm_fails(
    mocker: MockerFixture,
):
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads")
    _ = mocker.patch(
        "Ligare.AWS.ssm.SSMParameters.load_config",
        side_effect=Exception("Test mode failure."),
    )
    toml_mock = mocker.patch("toml.load")

    def use_configuration(
        config_builder: ConfigBuilder[Config], config_overrides: dict[str, Any]
    ) -> None:
        _ = config_builder.with_root_config(Config)

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .use_configuration(use_configuration)
        .use_filename("foo.toml")
    )

    _ = application_config_builder.build()

    assert toml_mock.called


def test__ApplicationConfigBuilder__build__calls_configuration_callback(
    mocker: MockerFixture,
):
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads")
    _ = mocker.patch("toml.load")

    use_configuration_mock = MagicMock()

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .use_configuration(use_configuration_mock)
        .use_filename("foo.toml")
    )

    with pytest.raises(Exception):
        _ = application_config_builder.build()

    use_configuration_mock.assert_called_once()
    call_args = use_configuration_mock.call_args.args
    assert isinstance(call_args[0], ConfigBuilder)
    assert isinstance(call_args[1], dict)


def test__ApplicationConfigBuilder__build__requires_root_config(
    mocker: MockerFixture,
):
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads")

    def use_configuration(
        config_builder: ConfigBuilder[Config], config_overrides: dict[str, Any]
    ) -> None:
        pass

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .use_configuration(use_configuration)
        .use_filename("foo.toml")
    )

    with pytest.raises(
        BuilderBuildError, match="`use_configuration` must be called"
    ) as e:
        _ = application_config_builder.build()

    assert isinstance(e.value.__cause__, ConfigBuilderStateError)


def test__ApplicationConfigBuilder__build__applies_additional_configs(
    mocker: MockerFixture,
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}, "test": {"foo": "bar"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    class TestConfig(BaseModel, AbstractConfig):
        @override
        def post_load(self) -> None:
            return super().post_load()

        foo: str

    def use_configuration(
        config_builder: ConfigBuilder[Config], config_overrides: dict[str, Any]
    ) -> None:
        _ = config_builder.with_root_config(Config).with_configs([TestConfig])

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .use_configuration(use_configuration)
        .use_filename("foo.toml")
    )
    config = application_config_builder.build()

    assert config is not None
    assert hasattr(config, "test")
    assert hasattr(getattr(config, "test"), "foo")
    assert getattr(getattr(config, "test"), "foo") == "bar"


def test__ApplicationConfigBuilder__build__applies_config_overrides(
    mocker: MockerFixture,
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    def use_configuration(
        config_builder: ConfigBuilder[Config], config_overrides: dict[str, Any]
    ) -> None:
        _ = config_builder.with_root_config(Config)
        config_overrides["logging"] = {"log_level": "INFO"}

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .use_configuration(use_configuration)
        .use_filename("foo.toml")
    )
    config = application_config_builder.build()

    assert config is not None
    assert hasattr(config, "logging")
    assert hasattr(getattr(config, "logging"), "log_level")
    assert getattr(getattr(config, "logging"), "log_level") == "INFO"


# FIXME move to application tests
def test__ApplicationBuilder__build__something(mocker: MockerFixture):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}, "flask": {"app_name": "app"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    def use_configuration(application_config_builder: ApplicationConfigBuilder[Config]):
        def use_configuration(
            config_builder: ConfigBuilder[Config], config_overrides: dict[str, Any]
        ) -> None:
            _ = config_builder.with_root_config(Config)

        _ = application_config_builder.use_configuration(
            use_configuration
        ).use_filename("foo.toml")

    application_builder = ApplicationBuilder[Flask, Config]().use_configuration(
        use_configuration
    )

    _ = (
        application_builder.with_flask_app_name("overridden_app")
        .with_flask_env("overridden_dev")
        .build()
    )
