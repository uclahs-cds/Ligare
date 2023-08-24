from BL_Python.web.config import load_config
from pytest_mock import MockerFixture


def test__Config__load_config__reads_toml_file(mocker: MockerFixture):
    fake_config_dict = {}
    toml_mock = mocker.patch("toml.load", return_value=fake_config_dict)
    _ = load_config("foo.toml")
    assert toml_mock.called


def test__Config__load_config__initializes_logging_config(mocker: MockerFixture):
    fake_config_dict = {"logging": {"log_level": "DEBUG"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config("foo.toml")
    assert config.logging.log_level == "DEBUG"


def test__Config__load_config__initializes_flask_config(mocker: MockerFixture):
    fake_config_dict = {"flask": {"app_name": "test_app"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config("foo.toml")
    assert config.flask is not None
    assert config.flask.app_name == "test_app"


def test__Config__load_config__initializes_database_config(mocker: MockerFixture):
    fake_config_dict = {"database": {"connection_string": "test_connection_string"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config("foo.toml")
    assert config.database is not None
    assert config.database.connection_string == "test_connection_string"


def test__Config__load_config__initializes_SAML2_config(mocker: MockerFixture):
    fake_config_dict = {"saml2": {"metadata": "test_metadata"}}
    _ = mocker.patch("io.open")
    _ = mocker.patch("toml.decoder.loads", return_value=fake_config_dict)
    config = load_config("foo.toml")
    assert config.saml2 is not None
    assert config.saml2.metadata == "test_metadata"
