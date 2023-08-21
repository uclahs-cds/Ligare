"""
Compound Assay Platform Flask application.

Flask entry point.
"""
import logging
from os import environ, path
from pprint import pprint
from typing import Optional, cast

import json_logging

# from CAP.app.blueprints.sso import *
# from CAP.app.dependencies import AppModule, AppSamlModule
# from CAP.app.handlers import (
#    register_api_request_handlers,
#    register_api_response_handlers,
#    register_app_teardown_handlers,
#    register_error_handlers,
# )
# from CAP.app.services.user.login_manager import LoginManager
# from CAP.database.models.CAP import Base
from connexion.apps.flask_app import FlaskApp
from flask import Flask
from flask_injector import FlaskInjector
from lib_programname import get_path_executed_script

from .config import Config, load_config
from .middleware import configure_dependencies, register_error_handlers

# from sqlalchemy.orm.scoping import ScopedSession

_get_program_dir = lambda: path.dirname(get_path_executed_script())
_get_exec_dir = lambda: path.abspath(".")


def create_app(
    config_filename: str = "config.toml",
):
    """
    Bootstrap the Flask applcation.

    Args:
        name: The name of the application. Replaces the value of `FLASK_APP` if not None.
        environment: The environment in which to run Flask. Can be one of `development`, `test`, or `production`. Replaces `FLASK_ENV` if not None.
    """

    config_overrides = {}
    if environ.get("FLASK_APP"):
        config_overrides["app_name"] = environ["FLASK_APP"]

    if environ.get("FLASK_ENV"):
        config_overrides["env"] = environ["FLASK_ENV"]

    config: Config
    if config_overrides:
        config = load_config(config_filename, {"flask": config_overrides})
    else:
        config = load_config(config_filename)

    if config.flask is None:
        raise Exception("You must set [flask] in the application configuration.")

    if not config.flask.app_name:
        raise Exception(
            "You must set the Flask application name in the [flask.app_name] config or FLASK_APP envvar."
        )

    app: Flask

    if config.flask.openapi is not None:
        if config.flask.openapi.spec_path is None:
            raise Exception(
                "When using OpenAPI with Flask, you must set spec_path in the config."
            )
        openapi: FlaskApp = configure_openapi(config, config.flask.app_name)
        app = cast(Flask, openapi.app)
    else:
        app = Flask(config.flask.app_name)
        config.update_flask_config(app.config)
        configure_blueprint_routes(app)

    register_error_handlers(app)
    # register_api_request_handlers(app)
    # register_api_response_handlers(app)
    # register_app_teardown_handlers(app)
    flask_injector = configure_dependencies(app, config)
    app.injector = flask_injector

    return app


def configure_openapi(config: Config, name: Optional[str] = None):
    """
    Instantiate Connexion and set Flask logging options
    """

    if config.flask is None or config.flask.openapi is None:
        raise Exception("OpenAPI configuration is empty.")

    # host configuration set up
    # TODO host/port setup should move into application initialization
    # and not be tied to connexion configuration
    host = "127.0.0.1"
    port = 5000
    # TODO replace SERVER_NAME with host/port in config
    if environ.get("SERVER_NAME") is not None:
        (host, port_str) = environ["SERVER_NAME"].split(":")
        port = int(port_str)

    # connexion and openapi set up
    # openapi_spec_dir: str = "app/swagger/"
    # if environ.get("OPENAPI_SPEC_DIR"):
    #    openapi_spec_dir = environ["OPENAPI_SPEC_DIR"]

    exec_dir = _get_exec_dir()

    connexion_app = FlaskApp(
        __name__ if name is None else name,
        # TODO support relative OPENAPI_SPEC_DIR and prepend program_dir?
        specification_dir=exec_dir,
        host=host,
        port=port,
    )
    app = cast(Flask, connexion_app.app)
    config.update_flask_config(app.config)

    # flask request log handler
    enable_json = not environ.get("PLAINTEXT_LOG_OUTPUT")
    # FIXME this errors in the new structure
    # json_logging.init_connexion(enable_json=enable_json)
    # json_logging.init_request_instrument(connexion_app)
    # if enable_json:
    #    json_logging.config_root_logger()
    app.logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())

    connexion_app.add_api(
        "src/" + config.flask.openapi.spec_path,
        base_path="/v1",
        validate_responses=config.flask.openapi.validate_responses,
        options={"swagger_ui": True},
    )

    return connexion_app


def configure_blueprint_routes(app: Flask, blueprint_import_subdir: str = "blueprints"):
    """
    Register Flask blueprints and API routes
    """
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    from flask import Blueprint

    program_dir = _get_program_dir()
    blueprint_import_dir = Path(program_dir, blueprint_import_subdir)

    module_paths = blueprint_import_dir.glob("*.py")

    for path in module_paths:
        if not (path.is_file() or path.name == "__init__.py"):
            continue
        # load the module from its path
        # and execute it
        spec = spec_from_file_location(path.name.rstrip(".py"), str(path))
        if spec is None or spec.loader is None:
            raise Exception(f"Module cannot be created from path {path}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        # find all Flask blueprints in
        # the module and register them
        for module_name, module_var in vars(module).items():
            if not (
                module_name.endswith("_blueprint") or isinstance(module_var, Blueprint)
            ):
                continue
            app.register_blueprint(cast(Blueprint, module_var))
