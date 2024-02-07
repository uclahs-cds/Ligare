import pytest
from BL_Python.programming.collections.dict import AnyDict
from BL_Python.programming.config import load_config
from BL_Python.web.config import Config
from pytest_mock import MockerFixture


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
    config = load_config(Config, "foo.toml")

    with pytest.raises(
        Exception, match=r"^`flask.session.cookie.secret_key` must be set in config.$"
    ):
        config.prepare_env_for_flask()
