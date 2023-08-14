"""
Compound Assay Platform Flask application.

Flask entry point.
"""

import logging
from os import environ, path
from typing import Optional, cast

import json_logging
from BL_Python.web.config import Config, load_config

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

# from sqlalchemy.orm.scoping import ScopedSession

_get_program_dir = lambda: path.dirname(get_path_executed_script())


def create_app(
    name: Optional[str] = None,
    environment: Optional[str] = None,
    config_filename: str = "config.toml",
):
    """
    Bootstrap the Flask applcation.

    Args:
        name: The name of the application. Replaces the value of `FLASK_APP` if not None.
        environment: The environment in which to run Flask. Can be one of `development`, `test`, or `production`. Replaces `FLASK_ENV` if not None.
    """

    config = load_config(config_filename)

    if config.flask is None:
        raise Exception("You must set [flask] in the application configuration.")

    # basic environment set up
    if name is not None:
        environ.update({"FLASK_APP": config.flask.app_name})

    if environment is not None:
        environ.update({"FLASK_ENV": config.flask.env})

    configure_logging()

    app: Flask
    if config.flask.openapi is not None:
        if config.flask.openapi.spec_path is None:
            raise Exception(
                "When using OpenAPI with Flask, you must set spec_path in the config."
            )
        openapi: FlaskApp = configure_openapi(name, config.flask.openapi.spec_path)
        app = cast(Flask, openapi.app)
        return openapi
    else:
        app = Flask(config.flask.app_name)
        configure_blueprint_routes(app)
        return app
    # register_error_handlers(app)
    # register_api_request_handlers(app)
    # register_api_response_handlers(app)
    # register_app_teardown_handlers(app)
    # flask_injector = configure_dependencies(app)

    # return (openapi, flask_injector)


def configure_logging():
    """
    Set root logging level and set log format to JSON
    """
    LOGLEVEL = environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(level=LOGLEVEL)


def configure_openapi(
    name: Optional[str] = None, openapi_spec_path: str = "openapi.yaml"
):
    """
    Instantiate Connexion and set Flask logging options
    """
    # host configuration set up
    # TODO host/port setup should move into application initialization
    # and not be tied to connexion configuration
    host = "127.0.0.1"
    port = 5000
    if environ.get("SERVER_NAME") is not None:
        (host, port_str) = environ["SERVER_NAME"].split(":")
        port = int(port_str)

    # connexion and openapi set up
    # openapi_spec_dir: str = "app/swagger/"
    # if environ.get("OPENAPI_SPEC_DIR"):
    #    openapi_spec_dir = environ["OPENAPI_SPEC_DIR"]

    program_dir = path.dirname(get_path_executed_script())

    connexion_app = FlaskApp(
        __name__ if name is None else name,
        # TODO support relative OPENAPI_SPEC_DIR and prepend program_dir?
        specification_dir=program_dir,
        host=host,
        port=port,
    )
    app = connexion_app.app
    # configure_flask_config(app)

    # flask request log handler
    enable_json = not environ.get("PLAINTEXT_LOG_OUTPUT")
    json_logging.init_connexion(enable_json=enable_json)
    json_logging.init_request_instrument(connexion_app)
    if enable_json:
        json_logging.config_root_logger()
    app.logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())

    validate_responses = app.config["VALIDATE_API_RESPONSES"]
    connexion_app.add_api(
        openapi_spec_path,
        base_path="/v1",
        validate_responses=validate_responses,
        options={"swagger_ui": True},
    )

    return connexion_app


def configure_flask_config(app: Flask):
    """
    Load the Config instance and set it in the Flask app
    """
    config = Config.get_env_config(app.config["ENV"])
    # FIXME this will not work with the new config classes
    app.config.from_object(config)


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


def configure_dependencies(app: Flask):
    """
    Configures dependency injection and registers all Flask
    application dependencies. The FlaskInjector instance
    can be used to bootstrap and start the Flask application.
    """
    # bootstrap the flask application and its dependencies
    flask_injector = FlaskInjector(
        app,
        [
            AppModule(app),
            AppSamlModule(
                metadata=app.config["SAML2_METADATA"]
                or app.config["SAML2_METADATA_URL"],
                settings=vars(app.config["SAML2_LOGGING"]),
            ),
        ],
    )

    app.secret_key = app.config["SECRET_KEY"]
    scoped_session: Optional[ScopedSession] = None
    try:
        # enable `Assay.query(...)`-stlye queries
        scoped_session = flask_injector.injector.get(ScopedSession)
        Base.query = scoped_session.query_property()

        # performs a side-effect by adding a property `login_manager` to `app`
        # injector is needed to instantiate dependencies for LoginManager
        # and its dependencies
        flask_injector.injector.get(LoginManager)
    except Exception:
        logging.exception("Could not initialize LoginManager.")
        raise
    finally:
        if scoped_session is not None:  # pyright: ignore[reportUnnecessaryComparison]
            scoped_session.remove()

    return flask_injector
