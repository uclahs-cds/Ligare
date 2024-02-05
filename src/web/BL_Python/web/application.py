"""
Compound Assay Platform Flask application.

Flask entry point.
"""

import logging
from dataclasses import dataclass
from os import environ, path
from typing import Generic, Optional, TypeVar, cast

import json_logging
from BL_Python.programming.config import AbstractConfig, ConfigBuilder, load_config
from BL_Python.programming.dependency_injection import ConfigModule
from connexion import FlaskApp
from flask import Blueprint, Flask
from flask_injector import FlaskInjector
from injector import Module
from lib_programname import get_path_executed_script

from .config import Config
from .middleware import (
    register_api_request_handlers,
    register_api_response_handlers,
    register_error_handlers,
)
from .middleware.dependency_injection import configure_dependencies

_get_program_dir = lambda: path.dirname(get_path_executed_script())
_get_exec_dir = lambda: path.abspath(".")

TApp = Flask | FlaskApp
T_app = TypeVar("T_app", bound=TApp, covariant=True)


@dataclass
class AppInjector(Generic[T_app]):
    app: T_app
    flask_injector: FlaskInjector


FlaskAppInjector = AppInjector[Flask]
OpenAPIAppInjector = AppInjector[FlaskApp]


@dataclass
class CreateAppResult(Generic[T_app]):
    flask_app: Flask
    app_injector: AppInjector[T_app]


# In Python 3.12 we can use generics in functions,
# but we target >= Python 3.10. This is one way
# around that limitation.
class App(Generic[T_app]):
    """
    Create a new generic type for the application instance.

    Type Args:
        T_app: Either `Flask` or `FlaskApp`
    """

    @staticmethod
    def create(
        config_filename: str = "config.toml",
        # FIXME should be a list of PydanticDataclass
        application_configs: list[type[AbstractConfig]] | None = None,
        application_modules: list[Module] | None = None,
    ) -> CreateAppResult[T_app]:
        """
        Bootstrap the Flask applcation.

        Args:
            config_filename: The name of the TOML file to load configuration information from.
            application_config: A list of Pydantic objects to store configuration information from the TOML file.
            application_modules: Modules the application will use for the application lifetime.
        """
        return cast(
            CreateAppResult[T_app],
            create_app(config_filename, application_configs, application_modules),
        )


def create_app(
    config_filename: str = "config.toml",
    # FIXME should be a list of PydanticDataclass
    application_configs: list[type[AbstractConfig]] | None = None,
    application_modules: list[Module] | None = None,
    # FIXME eventually should replace with builders
    # and configurators so this list of params doesn't
    # just grow and grow.
    # startup_builder: IStartupBuilder,
    # config: Config,
) -> CreateAppResult[TApp]:
    """
    Do not use this method directly. Instead, use `App[T_app].create()`
    """
    # set up the default configuration as soon as possible
    # also required to call before json_logging.config_root_logger()
    logging.basicConfig(force=True)

    config_overrides = {}
    if environ.get("FLASK_APP"):
        config_overrides["app_name"] = environ["FLASK_APP"]

    if environ.get("FLASK_ENV"):
        config_overrides["env"] = environ["FLASK_ENV"]

    config_type = Config
    if application_configs is not None:
        # fmt: off
        config_type = ConfigBuilder[Config]()\
            .with_root_config(Config)\
            .with_configs(application_configs)\
            .build()
        # fmt: on
    full_config: Config
    if config_overrides:
        full_config = load_config(
            config_type, config_filename, {"flask": config_overrides}
        )
    else:
        full_config = load_config(config_type, config_filename)

    full_config.prepare_env_for_flask()

    if full_config.flask is None:
        raise Exception("You must set [flask] in the application configuration.")

    if not full_config.flask.app_name:
        raise Exception(
            "You must set the Flask application name in the [flask.app_name] config or FLASK_APP envvar."
        )

    app: Flask | FlaskApp

    if full_config.flask.openapi is not None:
        openapi = configure_openapi(full_config)
        app = openapi
    else:
        app = configure_blueprint_routes(full_config)

    register_error_handlers(app)
    _ = register_api_request_handlers(app)
    _ = register_api_response_handlers(app)
    # register_app_teardown_handlers(app)

    # Register every subconfig as a ConfigModule.
    # This will allow subpackages to resolve their own config types,
    # allow for type safety against objects of those types.
    # Otherwise, they can resolve `AbstractConfig`, but then type
    # safety is lost.
    # Note that, if any `ConfigModule` is provided in `application_modules`,
    # those will override the automatically generated `ConfigModule`s.
    application_modules = [
        ConfigModule(config, type(config)) for (_, config) in full_config
    ] + (application_modules if application_modules else [])
    # The `full_config` module cannot be overridden unless the application
    # IoC container is fiddled with. `full_config` is the instance registered
    # to `AbstractConfig`.
    modules = application_modules + [ConfigModule(full_config, type(full_config))]
    flask_injector = configure_dependencies(app, application_modules=modules)

    flask_app = app.app if isinstance(app, FlaskApp) else app
    return CreateAppResult(flask_app, AppInjector(app, flask_injector))


def configure_openapi(config: Config, name: Optional[str] = None):
    """
    Instantiate Connexion and set Flask logging options
    """

    if (
        config.flask is None
        or config.flask.openapi is None
        or config.flask.openapi.spec_path is None
    ):
        raise Exception(
            "OpenAPI configuration is empty. Review the `openapi` section of your application's `config.toml`."
        )

    ## host configuration set up
    ## TODO host/port setup should move into application initialization
    ## and not be tied to connexion configuration
    # host = "127.0.0.1"
    # port = 5000
    ## TODO replace SERVER_NAME with host/port in config
    # if environ.get("SERVER_NAME") is not None:
    #    (host, port_str) = environ["SERVER_NAME"].split(":")
    #    port = int(port_str)

    # connexion and openapi set up
    # openapi_spec_dir: str = "app/swagger/"
    # if environ.get("OPENAPI_SPEC_DIR"):
    #    openapi_spec_dir = environ["OPENAPI_SPEC_DIR"]

    exec_dir = _get_exec_dir()

    connexion_app = FlaskApp(
        config.flask.app_name,
        # TODO support relative OPENAPI_SPEC_DIR and prepend program_dir?
        specification_dir=exec_dir,
        # host=host,
        # port=port,
    )
    app = connexion_app.app
    config.update_flask_config(app.config)

    enable_json_logging = config.logging.format == "JSON"
    if enable_json_logging:
        json_logging.init_connexion(  # pyright: ignore[reportUnknownMemberType]
            enable_json=enable_json_logging
        )
        json_logging.init_request_instrument(  # pyright: ignore[reportUnknownMemberType]
            connexion_app
        )
        json_logging.config_root_logger()  # pyright: ignore[reportUnknownMemberType]

    app.logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())

    options: dict[str, bool | str] = {
        "swagger_ui": config.flask.openapi.use_swagger,
        "swagger_url": config.flask.openapi.swagger_url or "/",
    }

    _ = connexion_app.add_api(
        f"{config.flask.app_name}/{config.flask.openapi.spec_path}",
        # base_path="/",
        validate_responses=config.flask.openapi.validate_responses,
        options=options,
    )

    # FIXME what's the new way to get this URL?
    # if config.flask.openapi.use_swagger:
    #    # App context needed for url_for.
    #    # This can only run after connexion is instantiated
    #    # because it registers the swagger UI url.
    #    with app.app_context():
    #        app.logger.info(
    #            f"Swagger UI can be accessed at {url_for('/./_swagger_ui_index', _external=True)}"
    #        )

    return connexion_app


def configure_blueprint_routes(
    config: Config, blueprint_import_subdir: str = "endpoints"
):
    """
    Register Flask blueprints and API routes
    """
    if config.flask is None:
        raise Exception(
            "Flask configuration is empty. Review the `flask` section of your application's `config.toml`."
        )

    app = Flask(config.flask.app_name)
    config.update_flask_config(app.config)

    enable_json_logging = config.logging.format == "JSON"
    if enable_json_logging:
        json_logging.init_flask(  # pyright: ignore[reportUnknownMemberType]
            enable_json=enable_json_logging
        )
        json_logging.init_request_instrument(  # pyright: ignore[reportUnknownMemberType]
            app
        )
        json_logging.config_root_logger()  # pyright: ignore[reportUnknownMemberType]

    blueprint_modules = _import_blueprint_modules(app, blueprint_import_subdir)
    _register_blueprint_modules(app, blueprint_modules)
    return app


def _import_blueprint_modules(app: Flask, blueprint_import_subdir: str):
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    from flask import Blueprint

    program_dir = _get_program_dir()
    blueprint_import_dir = Path(program_dir, blueprint_import_subdir)

    module_paths = blueprint_import_dir.glob("*.py")

    blueprint_modules: list[Blueprint] = []

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
            # TODO why did we allow _blueprint when it's not a Blueprint?
            if module_name.endswith("_blueprint") or isinstance(module_var, Blueprint):
                blueprint_modules.append(module_var)

    return blueprint_modules


def _register_blueprint_modules(app: Flask, blueprint_modules: list[Blueprint]):
    for module in blueprint_modules:
        app.register_blueprint(module)
