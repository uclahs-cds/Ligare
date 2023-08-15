import pytest
from BL_Python.web.application import create_app
from BL_Python.web.config import Config, FlaskConfig
from pytest_mock import MockerFixture


class TestCreateApp:
    def _get_basic_config(self):
        return Config(flask=FlaskConfig(app_name="test_app"))

    # https://stackoverflow.com/a/55079736
    # creates a fixture on this class called `setup_method_fixture`
    # then tells pytest to use it for every test in the class
    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, mocker: MockerFixture):
        _ = mocker.patch("io.open")
        _ = mocker.patch("toml.decoder.loads", return_value={})
        _ = mocker.patch(
            "BL_Python.web.application._get_program_dir", return_value="/dev/null"
        )
        pass

    def test__loads_config_from_toml(self, mocker: MockerFixture):
        load_config_mock = mocker.patch(
            "BL_Python.web.application.load_config",
            return_value=self._get_basic_config(),
        )

        toml_filename = (
            f"{TestCreateApp.test__loads_config_from_toml.__name__}-config.toml"
        )
        _ = create_app(config_filename=toml_filename)
        assert load_config_mock.called
        assert load_config_mock.call_args and load_config_mock.call_args[0]
        assert load_config_mock.call_args[0][0] == toml_filename

    @pytest.mark.parametrize(
        "envvar_name,config_var_name,var_value",
        [
            ("FLASK_APP", "app_name", "foobar"),
            ("FLASK_ENV", "env", "barfoo"),
        ],
    )
    def test__updates_flask_config_from_envvars(
        self,
        envvar_name: str,
        config_var_name: str,
        var_value: str,
        mocker: MockerFixture,
    ):
        config = self._get_basic_config()
        object.__setattr__(config.flask, config_var_name, var_value)
        from os import environ

        environ.update({envvar_name: var_value})
        _ = mocker.patch("BL_Python.web.application.load_config", return_value=config)
        _ = create_app()

        assert object.__getattribute__(config.flask, config_var_name) == var_value
