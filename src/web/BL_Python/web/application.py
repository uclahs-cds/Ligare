"""
Compound Assay Platform Flask application.

Flask entry point.
"""

import logging
from os import environ, path
from typing import Optional

import json_logging
from BL_Python.web.config import Config

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


def create_app(name: Optional[str] = None, environment: Optional[str] = None):
    """
    Bootstrap the Flask applcation.

    Args:
        name: The name of the application. Replaces the value of `FLASK_APP` if not None.
        environment: The environment in which to run Flask. Can be one of `development`, `test`, or `production`. Replaces `FLASK_ENV` if not None.
    """
    Config.initialize_env()

    # basic environment set up
    if name is not None:
        environ.update({"FLASK_APP": name})

    if environment is not None:
        environ.update({"FLASK_ENV": environment})

    config = Config.get_env_config(environ.get("FLASK_ENV"))

    configure_logging()

    if config.OPENAPI_SPEC_PATH:
        openapi = configure_openapi(name, config.OPENAPI_SPEC_PATH)

    app = openapi.app
    # configure_routes(app)
    # register_error_handlers(app)
    # register_api_request_handlers(app)
    # register_api_response_handlers(app)
    # register_app_teardown_handlers(app)
    # flask_injector = configure_dependencies(app)

    # return (openapi, flask_injector)
    return openapi


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
    configure_flask_config(app)

    # flask request log handler
    enable_json = not environ.get("PLAINTEXT_LOG_OUTPUT")
    json_logging.init_connexion(enable_json=enable_json)
    json_logging.init_request_instrument(connexion_app)
    if enable_json:
        json_logging.config_root_logger()
    app.logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())

    validate_responses = app.config["VALIDATE_API_RESPONSES"]
    #    connexion_app.add_api(
    #        "server.yaml",
    #        base_path="/",
    #        validate_responses=validate_responses,
    #        options={"swagger_ui": True},
    #    )
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
    app.config.from_object(config)


def configure_routes(app: Flask):
    """
    Register Flask blueprints and API routes
    """
    from CAP.app.blueprints import server

    app.register_blueprint(server.server_blueprint)

    from CAP.app.blueprints.v1 import technician

    app.register_blueprint(technician.technician_blueprint)

    from CAP.app.blueprints.sso import sso_blueprint

    app.register_blueprint(sso_blueprint)

    from CAP.app.blueprints.v1.admin import admin_blueprint

    app.register_blueprint(admin_blueprint)

    from CAP.app.blueprints.v1.analyst import analyst_blueprint

    app.register_blueprint(analyst_blueprint)

    from CAP.app.blueprints.v1.user import user_blueprint

    app.register_blueprint(user_blueprint)


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
