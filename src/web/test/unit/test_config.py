from os import environ

import pytest
from BL_Python.programming.collections.dict import AnyDict, merge
from BL_Python.programming.config import load_config
from BL_Python.testing.environ import (
    environ_resetter,  # pyright: ignore[reportUnusedImport]
)
from BL_Python.web.config import (
    Config,
    FlaskConfig,
    FlaskSessionConfig,
    FlaskSessionCookieConfig,
)
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


@pytest.mark.parametrize(
    "config_class", [FlaskConfig, FlaskSessionConfig, FlaskSessionCookieConfig]
)
def test__Config__prepare_env_for_flask__does_not_set_flask_envvars_when_flask_not_configured(
    config_class: Config,
    mocker: MockerFixture,
):
    fake_config_dict = {}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    sut = mocker.spy(config_class, "_prepare_env_for_flask")

    config = load_config(Config, "foo.toml")
    config.prepare_env_for_flask()

    assert config.flask is None
    sut.assert_not_called()


@pytest.mark.parametrize(
    "config_class", [FlaskConfig, FlaskSessionConfig, FlaskSessionCookieConfig]
)
def test__Config__prepare_env_for_flask__sets_flask_envvars_when_flask_configured(
    config_class: Config,
    mocker: MockerFixture,
):
    fake_config_dict = {
        "flask": {
            "app_name": "test_app",
            "session": {"cookie": {"secret_key": "abc123"}},
        }
    }

    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    sut = mocker.spy(config_class, "_prepare_env_for_flask")

    config = load_config(Config, "foo.toml")
    config.prepare_env_for_flask()

    assert config.flask is not None
    sut.assert_called()


@pytest.mark.parametrize(
    "key,envvar,set_value,get_value",
    [
        ("secret_key", "SECRET_KEY", "abc123", "abc123"),
        ("name", "SESSION_COOKIE_NAME", "session", "session"),
        ("name", "SESSION_COOKIE_NAME", "", ""),
        ("httponly", "SESSION_COOKIE_HTTPONLY", True, "1"),
        ("httponly", "SESSION_COOKIE_HTTPONLY", False, "0"),
        ("secure", "SESSION_COOKIE_SECURE", True, "1"),
        ("secure", "SESSION_COOKIE_SECURE", False, "0"),
        ("samesite", "SESSION_COOKIE_SAMESITE", "none", "none"),
        ("samesite", "SESSION_COOKIE_SAMESITE", "", ""),
    ],
)
def test__FlaskSessionCookieConfig__prepare_env_for_flask__sets_flask_envvars(
    key: str,
    envvar: str,
    set_value: str | bool,
    get_value: str | int,
    mocker: MockerFixture,
    environ_resetter: None,
):
    fake_config_dict = {
        "secret_key": "abc123",
        "name": "session",
        "httponly": True,
        "secure": True,
        "samesite": "none",
    }
    fake_config_dict = merge(fake_config_dict, {key: set_value})

    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    config = load_config(FlaskSessionCookieConfig, "foo.toml")

    config._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]
    assert environ[envvar] == get_value


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


@pytest.mark.parametrize(
    "key,envvar,set_value,get_value",
    [
        ("permanent", "PERMANENT_SESSION", True, "1"),
        ("permanent", "PERMANENT_SESSION", False, "0"),
        ("lifetime", "PERMANENT_SESSION_LIFETIME", 123, "123"),
        ("lifetime", "PERMANENT_SESSION_LIFETIME", 0, ""),
        ("refresh_each_request", "SESSION_REFRESH_EACH_REQUEST", True, "1"),
        ("refresh_each_request", "SESSION_REFRESH_EACH_REQUEST", False, "0"),
    ],
)
def test__FlaskSessionConfig__prepare_env_for_flask__sets_flask_envvars(
    key: str,
    envvar: str,
    set_value: str | bool,
    get_value: str | int,
    mocker: MockerFixture,
    environ_resetter: None,
):
    fake_config_dict = {
        "secret_key": "abc123",
        "name": "session",
        "httponly": True,
        "secure": True,
        "samesite": "none",
    }
    fake_config_dict = merge(
        fake_config_dict, {key: set_value, "cookie": {"secret_key": "abc123"}}
    )

    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    config = load_config(FlaskSessionConfig, "foo.toml")

    config._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]
    assert environ[envvar] == get_value


@pytest.mark.parametrize(
    "key,envvar,set_value,get_value",
    [
        ("app_name", "FLASK_APP", "test_app", "test_app"),
        ("env", "ENV", "development", "development"),
        ("host", "FLASK_RUN_HOST", "example.org", "example.org"),
        ("port", "FLASK_RUN_PORT", "5050", "5050"),
    ],
)
def test__FlaskConfig__prepare_env_for_flask__sets_flask_envvars(
    key: str,
    envvar: str,
    set_value: str | bool,
    get_value: str | int,
    mocker: MockerFixture,
    environ_resetter: None,
):
    fake_config_dict = {
        "secret_key": "abc123",
        "name": "session",
        "httponly": True,
        "secure": True,
        "samesite": "none",
    }
    fake_config_dict = merge(
        fake_config_dict,
        {key: set_value, "session": {"cookie": {"secret_key": "abc123"}}},
    )

    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    config = load_config(FlaskConfig, "foo.toml")

    config._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]
    assert environ[envvar] == get_value


@pytest.mark.parametrize(
    "config_class", [FlaskConfig, FlaskSessionConfig, FlaskSessionCookieConfig]
)
def test__Config__update_flask_config__does_not_set_flask_config_when_flask_not_configured(
    config_class: Config,
    mocker: MockerFixture,
):
    fake_config_dict = {}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    flask_config_mock = mocker.patch("BL_Python.web.config.FlaskAppConfig")
    sut = mocker.spy(config_class, "_update_flask_config")

    config = load_config(Config, "foo.toml")
    config.update_flask_config(flask_config_mock)

    assert config.flask is None
    sut.assert_not_called()


@pytest.mark.parametrize(
    "config_class", [FlaskConfig, FlaskSessionConfig, FlaskSessionCookieConfig]
)
def test__Config__update_flask_config__sets_flask_config_when_flask_configured(
    config_class: Config,
    mocker: MockerFixture,
):
    fake_config_dict = {
        "flask": {
            "app_name": "test_app",
            "session": {"cookie": {"secret_key": "abc123"}},
        }
    }
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)

    flask_config_mock = mocker.patch("BL_Python.web.config.FlaskAppConfig")
    sut = mocker.spy(config_class, "_update_flask_config")

    config = load_config(Config, "foo.toml")
    config.update_flask_config(flask_config_mock)

    assert config.flask is not None
    sut.assert_called()
