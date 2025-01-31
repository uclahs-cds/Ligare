import pytest
from Ligare.programming.collections.dict import AnyDict
from Ligare.programming.config import AbstractConfig, load_config
from Ligare.programming.exception import BuilderBuildError, InvalidBuilderStateError
from Ligare.web.application import ApplicationConfigBuilder
from Ligare.web.config import Config
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
        _ = load_config(Config, "foo.toml")


@pytest.mark.parametrize("mode", ["ssm", "filename"])
def test__ApplicationConfigBuilder__build__succeeds_with_either_ssm_or_filename(
    mode: str, mocker: MockerFixture
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    _ = mocker.patch("Ligare.AWS.ssm.SSMParameters.load_config")

    application_config_builder = ApplicationConfigBuilder[Config]()

    if mode == "ssm":
        _ = application_config_builder.enable_ssm(True)
    else:
        _ = application_config_builder.with_config_filename("foo.toml")

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

    application_config_builder = ApplicationConfigBuilder[Config]().enable_ssm(True)

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

    application_config_builder = ApplicationConfigBuilder[
        Config
    ]().with_config_filename("foo.toml")

    _ = application_config_builder.build()

    assert toml_mock.called


def test__ApplicationConfigBuilder__build__applies_additional_configs(
    mocker: MockerFixture,
):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}, "test": {"foo": "bar"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    class TestConfig(AbstractConfig):
        @override
        def post_load(self) -> None:
            return super().post_load()

        foo: str

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .with_config_type(TestConfig)
        .with_config_filename("foo.toml")
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

    application_config_builder = (
        ApplicationConfigBuilder[Config]()
        .with_config_value_overrides({"logging": {"log_level": "INFO"}})
        .with_config_filename("foo.toml")
    )
    config = application_config_builder.build()

    assert config is not None
    assert hasattr(config, "logging")
    assert hasattr(getattr(config, "logging"), "log_level")
    assert getattr(getattr(config, "logging"), "log_level") == "INFO"
