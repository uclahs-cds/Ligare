import pathlib
from pathlib import Path
from typing import cast

import pytest
from flask import Blueprint
from Ligare.programming.config.exceptions import ConfigInvalidError
from Ligare.web.application import configure_blueprint_routes
from Ligare.web.config import Config, FlaskConfig
from Ligare.web.testing.create_app import (
    CreateFlaskApp,
    FlaskClientInjectorConfigurable,
)
from mock import MagicMock
from pytest_mock import MockerFixture


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
