"""
Compound Assay Platform Flask application.

Flask entry point.
"""
from os import environ, path
from typing import Optional, cast

from BL_Python.programming.config import AbstractConfig, ConfigBuilder, load_config
from BL_Python.programming.dependency_injection import ConfigModule

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
from flask import Flask, url_for
from injector import Module
from lib_programname import get_path_executed_script

# from .config import Config, ConfigBuilder, load_config
from .config import Config
from .middleware import (
    configure_dependencies,
    register_api_request_handlers,
    register_api_response_handlers,
    register_error_handlers,
)

_get_program_dir = lambda: path.dirname(get_path_executed_script())
_get_exec_dir = lambda: path.abspath(".")


def create_app(
    config_filename: str = "config.toml",
    # FIXME should be a list of PydanticDataclass
    application_configs: list[type[AbstractConfig]] | None = None,
    application_modules: list[Module] | None = None
    # FIXME eventually should replace with builders
    # and configurators so this list of params doesn't
    # just grow and grow.
    # startup_builder: IStartupBuilder,
    # config: Config,
) -> Flask:
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

    app: Flask

    if full_config.flask.openapi is not None:
        openapi: FlaskApp = configure_openapi(full_config, full_config.flask.app_name)
        app = cast(Flask, openapi.app)
    else:
        app = Flask(full_config.flask.app_name)
        full_config.update_flask_config(app.config)
        configure_blueprint_routes(app)

    register_error_handlers(app)
    register_api_request_handlers(app)
    register_api_response_handlers(app)
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
    modules = application_modules + [ConfigModule(full_config)]
    flask_injector = configure_dependencies(app, application_modules=modules)
    app.injector = flask_injector

    return app


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
    # enable_json = not environ.get("PLAINTEXT_LOG_OUTPUT")
    # FIXME this errors in the new structure
    # json_logging.init_connexion(enable_json=enable_json)
    # json_logging.init_request_instrument(connexion_app)
    # if enable_json:
    #    json_logging.config_root_logger()
    app.logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())

    options: dict[str, bool | str] = {
        "swagger_ui": config.flask.openapi.use_swagger,
        "swagger_url": config.flask.openapi.swagger_url or "/",
    }

    _ = connexion_app.add_api(
        f"{config.flask.app_name}/{config.flask.openapi.spec_path}",
        base_path="/",
        validate_responses=config.flask.openapi.validate_responses,
        options=options,
    )

    if config.flask.openapi.use_swagger:
        # App context needed for url_for.
        # This can only run after connexion is instantiated
        # because it registers the swagger UI url.
        with app.app_context():
            app.logger.info(
                f"Swagger UI can be accessed at {url_for('/./_swagger_ui_index', _external=True)}"
            )

    return connexion_app


def configure_blueprint_routes(app: Flask, blueprint_import_subdir: str = "endpoints"):
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


# class ConfigurationBuilder:
#    _DEFAULT_CONFIG_FILENAME = "config.toml"
#
#    def __init__(self) -> None:
#        self._config_filename = ConfigurationBuilder._DEFAULT_CONFIG_FILENAME
#
#    def use_config_file(self, config_filename: str):
#        self._config_filename = config_filename
#
#    def add_config(self, config: Config):
#        pass
#
#    def build(self) -> Config:
#        return load_config(self._config_filename)
#
#
# class ApplicationBuilder:
#    _configuration_callback: Callable[[ConfigurationBuilder], None] | None = None
#
#    def use_config(
#        self,
#        configuration_callback: Callable[[ConfigurationBuilder], None],
#    ):
#        self._configuration_callback = configuration_callback
#        return self
#
#    def build(self):
#        configuration_builder = ConfigurationBuilder()
#        configuration: Config
#        if self._configuration_callback is not None:
#            self._configuration_callback(configuration_builder)
#        configuration = configuration_builder.build()
#
#        return create_app(configuration)
#
#
# class IStartup(Protocol):
#    #    def configure_dependencies(self, services: BlappServices):
#    #        ...
#
#    def configure_application(self, app_builder: ApplicationBuilder):
#        ...
#
#
# class IStartupBuilder(Protocol):
#    def __init__(self, startup: Type[IStartup]) -> None:
#        ...
#
#    def build(self) -> Flask:
#        ...
#
#
# class StartupBuilder:
#    _application: IStartup
#
#    def __init__(self, startup: Type[IStartup]) -> None:
#        # TODO replace `object()` with the config object
#        self._application = startup()
#
#    def build(self):
#        # service_registry = BlappServices()
#        application_builder = ApplicationBuilder()
#
#        # self._application.configure_dependencies(service_registry)
#        self._application.configure_application(application_builder)
#
#        return application_builder.build()
#
#
# class Startup:
#    def configure_application(self, app_builder: ApplicationBuilder):
#        app_builder.use_config()
#        pass
#
#    def build(self):
#        pass
#
#
# test_app = create_app(StartupBuilder(Startup))
#
