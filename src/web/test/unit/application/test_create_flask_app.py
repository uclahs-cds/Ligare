import pathlib
from os import environ
from pathlib import Path
from typing import cast

import pytest
from flask import Blueprint, Flask
from Ligare.programming.config import AbstractConfig
from Ligare.programming.config.exceptions import ConfigInvalidError
from Ligare.programming.str import get_random_str
from Ligare.web.application import App  # pyright: ignore[reportDeprecated]
from Ligare.web.application import configure_blueprint_routes
from Ligare.web.config import Config, FlaskConfig
from Ligare.web.testing.create_app import (
    CreateFlaskApp,
    FlaskClientInjectorConfigurable,
)
from mock import MagicMock
from pydantic import BaseModel
from pytest_mock import MockerFixture
from typing_extensions import override


class TestCreateFlaskApp(CreateFlaskApp):
    def test__CreateFlaskApp__configure_blueprint_routes__requires_flask_config(self):
        with pytest.raises(
            Exception,
            match=r"^Flask configuration is empty\. Review the `flask` section of your application's `config\.toml`\.$",
        ):
            _ = configure_blueprint_routes(Config())

    def test__CreateFlaskApp__configure_blueprint_routes__creates_flask_app_using_config(
        self, mocker: MockerFixture
    ):
        _ = mocker.patch("Ligare.web.application.json_logging")
        flask_mock = mocker.patch("Ligare.web.application.Flask")

        app_name = f"{TestCreateFlaskApp.test__CreateFlaskApp__configure_blueprint_routes__creates_flask_app_using_config.__name__}-app_name"

        _ = configure_blueprint_routes(Config(flask=FlaskConfig(app_name=app_name)))

        flask_mock.assert_called_with(app_name)

    @pytest.mark.parametrize("filename", ["foo", "foo.py", "__main__.py"])
    def test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_ignores_directories_in_path(
        self, filename: str, mocker: MockerFixture
    ):
        mocker.stop(
            self._automatic_mocks["Ligare.web.application._import_blueprint_modules"]
        )

        spec_lookup_mock = mocker.patch("importlib.util.spec_from_file_location")
        glob_item_mock = MagicMock(
            is_file=MagicMock(
                # fakes a directory
                return_value=False
            )
        )
        type(glob_item_mock).name = filename

        app_name = f"{TestCreateFlaskApp.test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_ignores_directories_in_path.__name__}-app_name"

        _path = Path
        _ = mocker.patch(
            "pathlib.Path",
            return_value=MagicMock(
                glob=MagicMock(return_value=[glob_item_mock]),
            ),
        )

        try:
            flask_app = configure_blueprint_routes(
                Config(
                    flask=FlaskConfig(app_name=app_name),
                ),
                ".",
            )
        finally:
            # mocker doesn't appear to restore pathlib.Path correctly
            # either through automatic cleanup, `with` statements,
            # or `mocker.stop`.
            pathlib.Path = _path

        assert not spec_lookup_mock.called
        assert flask_app.blueprints == {}

    @pytest.mark.parametrize(
        "is_file,filename",
        [
            (True, "foo"),
            (True, "foo.py"),
            (True, "__main__.py"),
            (True, "__init__.py"),
            (False, "__init__.py"),
        ],
    )
    def test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_registers_python_files_and_modules(
        self, is_file: bool, filename: str, mocker: MockerFixture
    ):
        mocker.stop(
            self._automatic_mocks["Ligare.web.application._import_blueprint_modules"]
        )

        glob_item_mock = MagicMock(
            is_file=MagicMock(
                # fakes a directory
                return_value=is_file
            )
        )
        type(glob_item_mock).name = filename

        spec_lookup_mock = mocker.patch("importlib.util.spec_from_file_location")
        _ = mocker.patch("importlib.util.module_from_spec")

        app_name = f"{TestCreateFlaskApp.test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_registers_python_files_and_modules.__name__}-app_name"

        _ = mocker.patch(
            "pathlib.Path",
            return_value=MagicMock(
                glob=MagicMock(return_value=[glob_item_mock]),
            ),
        )

        _path = Path
        try:
            flask_app = configure_blueprint_routes(
                Config(
                    flask=FlaskConfig(app_name=app_name),
                ),
                ".",
            )
        finally:
            # mocker doesn't appear to restore pathlib.Path correctly
            # either through automatic cleanup, `with` statements,
            # or `mocker.stop`.
            pathlib.Path = _path

        spec_lookup_mock.assert_called()
        assert flask_app.blueprints == {}

    @pytest.mark.parametrize(
        "is_file,filename",
        [
            (True, "foo"),
            (True, "foo.py"),
            (True, "__main__.py"),
            (True, "__init__.py"),
            (False, "__init__.py"),
        ],
    )
    def test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_registers_blueprint_modules(
        self, is_file: bool, filename: str, mocker: MockerFixture
    ):
        mocker.stop(
            self._automatic_mocks["Ligare.web.application._import_blueprint_modules"]
        )
        _ = mocker.patch("importlib.util.spec_from_file_location")
        _ = mocker.patch("flask.app.Flask.register_blueprint")

        glob_item_mock = MagicMock(
            is_file=MagicMock(
                # fakes a directory
                return_value=is_file
            )
        )
        type(glob_item_mock).name = filename

        blueprint = Blueprint("foo_blueprint", "")
        _ = mocker.patch(
            "importlib.util.module_from_spec",
            return_value=MagicMock(foo_blueprint=blueprint),
        )

        app_name = f"{TestCreateFlaskApp.test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_registers_blueprint_modules.__name__}-app_name"

        _path = Path
        _ = mocker.patch(
            "pathlib.Path",
            return_value=MagicMock(
                glob=MagicMock(return_value=[glob_item_mock, glob_item_mock]),
            ),
        )

        try:
            flask_app = configure_blueprint_routes(
                Config(
                    flask=FlaskConfig(app_name=app_name),
                ),
                ".",
            )
        finally:
            # mocker doesn't appear to restore pathlib.Path correctly
            # either through automatic cleanup, `with` statements,
            # or `mocker.stop`.
            pathlib.Path = _path

        assert cast(MagicMock, flask_app.register_blueprint).call_count == 2
        cast(MagicMock, flask_app.register_blueprint).assert_called_with(blueprint)

    def test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_stops_when_module_load_fails(
        self, mocker: MockerFixture
    ):
        mocker.stop(
            self._automatic_mocks["Ligare.web.application._import_blueprint_modules"]
        )

        glob_item_mock = MagicMock(
            is_file=MagicMock(
                # fakes a directory
                return_value=True
            )
        )
        type(glob_item_mock).name = "__init__.py"
        _ = mocker.patch("importlib.util.spec_from_file_location", return_value=None)
        _ = mocker.patch("importlib.util.module_from_spec")

        _path = Path
        _ = mocker.patch(
            "pathlib.Path",
            return_value=MagicMock(
                glob=MagicMock(return_value=[glob_item_mock]),
            ),
        )
        app_name = f"{TestCreateFlaskApp.test__CreateFlaskApp__configure_blueprint_routes__when_discovering_blueprints_stops_when_module_load_fails.__name__}-app_name"

        with pytest.raises(
            Exception,
            match=rf"^Module cannot be created from path {glob_item_mock}$",
        ):
            try:
                _ = configure_blueprint_routes(
                    Config(
                        flask=FlaskConfig(app_name=app_name),
                    ),
                    ".",
                )
            finally:
                # mocker doesn't appear to restore pathlib.Path correctly
                # either through automatic cleanup, `with` statements,
                # or `mocker.stop`.
                pathlib.Path = _path

    def test__CreateFlaskApp__create_app__requires_flask_config(
        self, flask_client_configurable: FlaskClientInjectorConfigurable
    ):
        with pytest.raises(
            ConfigInvalidError,
            match=r"^You must set \[flask\] in the application configuration\.",
        ):
            _ = next(flask_client_configurable(Config()))

    def test__CreateFlaskApp__create_app__loads_config_from_toml(
        self, basic_config: Config, mocker: MockerFixture
    ):
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        load_config_mock = mocker.patch(
            "Ligare.web.application.load_config", return_value=basic_config
        )

        toml_filename = f"{TestCreateFlaskApp.test__CreateFlaskApp__create_app__loads_config_from_toml.__name__}-config.toml"
        _ = App[Flask].create(config_filename=toml_filename)  # pyright: ignore[reportDeprecated]
        assert load_config_mock.called
        assert load_config_mock.call_args and load_config_mock.call_args[0]
        assert load_config_mock.call_args[0][1] == toml_filename

    def test__CreateFlaskApp__create_app__uses_custom_config_types(
        self, mocker: MockerFixture
    ):
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        toml_filename = f"{TestCreateFlaskApp.test__CreateFlaskApp__create_app__uses_custom_config_types.__name__}-config.toml"
        toml_load_result = {
            "flask": {
                "app_name": f"{TestCreateFlaskApp.test__CreateFlaskApp__create_app__uses_custom_config_types.__name__}-app_name"
            },
            "custom": {"foo": get_random_str(k=26)},
        }

        _ = mocker.patch("toml.load", return_value=toml_load_result)

        class CustomConfig(BaseModel, AbstractConfig):
            @override
            def post_load(self) -> None:
                return super().post_load()

            foo: str = get_random_str(k=26)

        app = App[Flask].create(  # pyright: ignore[reportDeprecated]
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
    def test__CreateFlaskApp__create_app__updates_flask_config_from_envvars(
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
        _ = App[Flask].create()  # pyright: ignore[reportDeprecated]

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
    def test__CreateFlaskApp__create_app__requires_application_name(
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
                _ = App[Flask].create()  # pyright: ignore[reportDeprecated]
        else:
            _ = App[Flask].create()  # pyright: ignore[reportDeprecated]

    def test__CreateFlaskApp__create_app__configures_appropriate_app_type_based_on_config(
        self, mocker: MockerFixture
    ):
        toml_filename = f"{TestCreateFlaskApp.test__CreateFlaskApp__create_app__configures_appropriate_app_type_based_on_config.__name__}-config.toml"
        app_name = f"{TestCreateFlaskApp.test__CreateFlaskApp__create_app__configures_appropriate_app_type_based_on_config.__name__}-app_name"
        _ = mocker.patch(
            "Ligare.web.application.SSMParameters",
            return_value=MagicMock(load_config=MagicMock(return_value=None)),
        )
        _ = mocker.patch("Ligare.web.application.register_error_handlers")
        _ = mocker.patch("Ligare.web.application.register_api_request_handlers")
        _ = mocker.patch("Ligare.web.application.register_api_response_handlers")
        _ = mocker.patch("Ligare.web.application.configure_dependencies")

        configure_method_mock = mocker.patch(
            "Ligare.web.application.configure_blueprint_routes"
        )
        config = Config(flask=FlaskConfig(app_name=app_name))
        _ = mocker.patch("Ligare.web.application.load_config", return_value=config)
        _ = App[Flask].create(config_filename=toml_filename)  # pyright: ignore[reportDeprecated]

        configure_method_mock.assert_called_once_with(config)
