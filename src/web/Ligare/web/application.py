import logging
from collections import defaultdict
from dataclasses import dataclass
from os import environ, path
from typing import (
    Any,
    Generator,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    cast,
    final,
    overload,
)

import json_logging
from connexion import FlaskApp
from flask import Blueprint, Flask
from flask_injector import FlaskInjector
from injector import Module
from lib_programname import get_path_executed_script
from Ligare.AWS.ssm import SSMParameters
from Ligare.programming.collections.dict import NestedDict
from Ligare.programming.config import (
    AbstractConfig,
    ConfigBuilder,
    TConfig,
    load_config,
)
from Ligare.programming.config.exceptions import ConfigBuilderStateError
from Ligare.programming.dependency_injection import ConfigModule
from Ligare.programming.patterns.dependency_injection import ConfigurableModule
from Ligare.web.exception import BuilderBuildError, InvalidBuilderStateError
from typing_extensions import Self, deprecated

from .config import Config
from .middleware import (
    register_api_request_handlers,
    register_api_response_handlers,
    register_context_middleware,
    register_error_handlers,
)
from .middleware.dependency_injection import configure_dependencies

_get_program_dir = lambda: path.dirname(get_path_executed_script())
_get_exec_dir = lambda: path.abspath(".")

TApp = Flask | FlaskApp
T_app = TypeVar("T_app", bound=TApp)

TAppConfig = TypeVar("TAppConfig", bound=Config)


@dataclass
class AppInjector(Generic[T_app]):
    """
    Contains an instantiated `T_app` application in `app`,
    and its associated `FlaskInjector` IoC container.

    :param T_app Generic: An instance of Flask or FlaskApp.
    :param flask_inject FlaskInject: The applications IoC container.
    """

    app: T_app
    flask_injector: FlaskInjector


@dataclass
class CreateAppResult(Generic[T_app]):
    """
    Contains an instantiated Flask application and its
    associated application "container." This is either
    the same Flask instance, or an OpenAPI application.

    :param flask_app Generic: The Flask application.
    :param app_injector AppInjector[T_app]: The application's wrapper and IoC container.
    """

    flask_app: Flask
    app_injector: AppInjector[T_app]


FlaskAppResult = CreateAppResult[Flask]
OpenAPIAppResult = CreateAppResult[FlaskApp]


# In Python 3.12 we can use generics in functions,
# but we target >= Python 3.10. This is one way
# around that limitation.
@deprecated("`App` is deprecated. Use `ApplicationBuilder`.")
class App(Generic[T_app]):
    """
    Create a new generic type for the application instance.

    Type Args:
        T_app: Either `Flask` or `FlaskApp`
    """

    @deprecated("`App.create` is deprecated. Use `ApplicationBuilder`.")
    @staticmethod
    def create(
        config_filename: str = "config.toml",
        # FIXME should be a list of PydanticDataclass
        application_configs: list[type[AbstractConfig]] | None = None,
        application_modules: list[Module | type[Module]] | None = None,
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
            _create_app(config_filename, application_configs, application_modules),
        )


class UseConfigurationCallback(Protocol[TConfig]):
    """
    The callback for configuring an application's configuration.

    :param TConfig Protocol: The AbstractConfig type to be configured.
    """

    def __call__(
        self,
        config_builder: ConfigBuilder[TConfig],
        config_overrides: dict[str, Any],
    ) -> "None | ConfigBuilder[TConfig]":
        """
        Set up parameters for the application's configuration.

        :param ConfigBuilder[TConfig] config_builder: The ConfigBuilder instance.
        :param dict[str, Any] config_overrides: A dictionary of key/values that are applied over all keys that might exist in an instantiated config.
        :raises InvalidBuilderStateError: Upon a call to `build()`, the builder is misconfigured.
        :raises BuilderBuildError: Upon a call to `build()`, a failure occurred during the instantiation of the configuration.
        :raises Exception: Upon a call to `build()`, an unknown error occurred.
        :return None | ConfigBuilder[TConfig]: The callback may return `None` or the received `ConfigBuilder` instance so as to support the use of lambdas. This return value is not used.
        """


@final
class ApplicationConfigBuilder(Generic[TConfig]):
    _DEFAULT_CONFIG_FILENAME: str = "config.toml"

    def __init__(self) -> None:
        self._config_value_overrides: dict[str, Any] = {}
        self._config_builder: ConfigBuilder[TConfig] = ConfigBuilder[TConfig]()
        self._config_filename: str = ApplicationConfigBuilder._DEFAULT_CONFIG_FILENAME
        self._use_filename: bool = False
        self._use_ssm: bool = False

    def with_config_builder(self, config_builder: ConfigBuilder[TConfig]) -> Self:
        self._config_builder = config_builder
        return self

    def with_root_config_type(self, config_type: type[TConfig]) -> Self:
        _ = self._config_builder.with_root_config(config_type)
        return self

    def with_config_types(self, configs: list[type[AbstractConfig]] | None) -> Self:
        _ = self._config_builder.with_configs(configs)
        return self

    def with_config_type(self, config_type: type[AbstractConfig]) -> Self:
        _ = self._config_builder.with_config(config_type)
        return self

    def with_config_value_overrides(self, values: dict[str, Any]) -> Self:
        self._config_value_overrides = values
        return self

    def with_config_filename(self, filename: str) -> Self:
        self._config_filename = filename
        self._use_filename = True
        return self

    def enable_ssm(self, value: bool) -> Self:
        """
        Try to load config from AWS SSM. If `use_filename` was configured,
        a failed attempt to load from SSM will instead attempt to load from
        the configured filename. If `use_filename` is not configured and SSM
        fails, an exception is raised. If SSM succeeds, `build` will not
        load from the configured filename.

        :param bool value: Whether to use SSM
        :return Self:
        """
        self._use_ssm = value
        return self

    def build(self) -> TConfig | None:
        if not (self._use_ssm or self._use_filename):
            raise InvalidBuilderStateError(
                "Cannot build the application config without either `use_ssm` or `use_filename` having been configured."
            )

        try:
            config_type = self._config_builder.build()
        except ConfigBuilderStateError as e:
            raise BuilderBuildError(
                "A root config must be specified using `with_root_config` before calling `build()`."
            ) from e

        full_config: TConfig | None = None
        SSM_FAIL_ERROR_MSG = "Unable to load configuration. SSM parameter load failed and the builder is configured not to load from a file."
        if self._use_ssm:
            try:
                # requires that aws-ssm.ini exists and is correctly configured
                ssm_parameters = SSMParameters()
                full_config = ssm_parameters.load_config(config_type)

                if not self._use_filename and full_config is None:
                    raise BuilderBuildError(SSM_FAIL_ERROR_MSG)
            except Exception as e:
                if self._use_filename:
                    logging.getLogger().info("SSM parameter load failed.", exc_info=e)
                else:
                    raise BuilderBuildError(SSM_FAIL_ERROR_MSG) from e

        if self._use_filename and full_config is None:
            if self._config_value_overrides:
                full_config = load_config(
                    config_type, self._config_filename, self._config_value_overrides
                )
            else:
                full_config = load_config(config_type, self._config_filename)

        return full_config


class ApplicationConfigBuilderCallback(Protocol[TAppConfig]):
    def __call__(
        self,
        config_builder: ApplicationConfigBuilder[TAppConfig],
    ) -> "None | ApplicationConfigBuilder[TAppConfig]": ...


@final
class ApplicationBuilder(Generic[T_app]):
    def __init__(self) -> None:
        self._modules: list[Module | type[Module]] = []
        self._config_overrides: dict[str, Any] = {}

    _APPLICATION_CONFIG_BUILDER_PROPERTY_NAME: str = "__application_config_builder"

    @property
    def _application_config_builder(self) -> ApplicationConfigBuilder[Config]:
        builder = getattr(
            self, ApplicationBuilder._APPLICATION_CONFIG_BUILDER_PROPERTY_NAME, None
        )

        if builder is None:
            builder = ApplicationConfigBuilder[Config]()
            self._application_config_builder = builder.with_root_config_type(Config)

        return builder

    @_application_config_builder.setter
    def _application_config_builder(self, value: ApplicationConfigBuilder[Config]):
        setattr(
            self, ApplicationBuilder._APPLICATION_CONFIG_BUILDER_PROPERTY_NAME, value
        )

    @overload
    def with_module(self, module: Module) -> Self: ...
    @overload
    def with_module(self, module: type[Module]) -> Self: ...
    def with_module(self, module: Module | type[Module]) -> Self:
        module_type = type(module) if isinstance(module, Module) else module
        if issubclass(module_type, ConfigurableModule):
            _ = self._application_config_builder.with_config_type(
                module_type.get_config_type()
            )

        self._modules.append(module)
        return self

    def with_modules(self, modules: list[Module | type[Module]] | None) -> Self:
        if modules is not None:
            for module in modules:
                _ = self.with_module(module)
        return self

    @overload
    def use_configuration(
        self,
        __application_config_builder_callback: ApplicationConfigBuilderCallback[Config],
    ) -> Self:
        """
        Execute changes to the builder's `ApplicationConfigBuilder[TAppConfig]` instance.

        `__builder_callback` can return `None`, or the instance of `ApplicationConfigBuilder[TAppConfig]` passed to its `config_builder` argument.
        This allowance is so lambdas can be used; `ApplicationBuilder[T_app, TAppConfig]` does not use the return value.
        """
        ...

    @overload
    def use_configuration(
        self, __application_config_builder: ApplicationConfigBuilder[Config]
    ) -> Self:
        """Replace the builder's default `ApplicationConfigBuilder[TAppConfig]` instance, or any instance previously assigned."""
        ...

    def use_configuration(
        self,
        application_config_builder: ApplicationConfigBuilderCallback[Config]
        | ApplicationConfigBuilder[Config],
    ) -> Self:
        if callable(application_config_builder):
            _ = application_config_builder(self._application_config_builder)
        else:
            self._application_config_builder = application_config_builder

        return self

    def with_flask_app_name(self, value: str | None) -> Self:
        self._config_overrides["app_name"] = value
        return self

    def with_flask_env(self, value: str | None) -> Self:
        self._config_overrides["env"] = value
        return self

    def build(self) -> CreateAppResult[T_app]:
        config_overrides: NestedDict[str, Any] = defaultdict(dict)

        if (
            override_app_name := self._config_overrides.get("app_name", None)
        ) is not None and override_app_name != "":
            config_overrides["flask"]["app_name"] = override_app_name

        if (
            override_env := self._config_overrides.get("env", None)
        ) is not None and override_env != "":
            config_overrides["flask"]["env"] = override_env

        _ = self._application_config_builder.with_config_value_overrides(
            config_overrides
        )
        config = self._application_config_builder.build()

        if config is None:
            raise BuilderBuildError(
                "Failed to load the application configuration correctly."
            )

        if config.flask is None:
            raise Exception("You must set [flask] in the application configuration.")

        if not config.flask.app_name:
            raise Exception(
                "You must set the Flask application name in the [flask.app_name] config or FLASK_APP envvar."
            )

        app: T_app

        if config.flask.openapi is not None:
            openapi = configure_openapi(config)
            app = cast(T_app, openapi)
        else:
            app = cast(T_app, configure_blueprint_routes(config))

        register_error_handlers(app)
        _ = register_api_request_handlers(app)
        _ = register_api_response_handlers(app)
        _ = register_context_middleware(app)

        application_modules = [
            ConfigModule(config, type(config))
            for (_, config) in cast(
                Generator[tuple[str, AbstractConfig], None, None], config
            )
        ] + (self._modules if self._modules else [])
        # The `config` module cannot be overridden unless the application
        # IoC container is fiddled with. `config` is the instance registered
        # to `AbstractConfig`.
        modules = application_modules + [ConfigModule(config, Config)]
        flask_injector = configure_dependencies(app, application_modules=modules)

        flask_app = app.app if isinstance(app, FlaskApp) else app
        return CreateAppResult[T_app](
            flask_app, AppInjector[T_app](app, flask_injector)
        )


@deprecated("`create_app` is deprecated. Use `ApplicationBuilder`.")
def create_app(
    config_filename: str = "config.toml",
    # FIXME should be a list of PydanticDataclass
    application_configs: list[type[AbstractConfig]] | None = None,
    application_modules: list[Module | type[Module]] | None = None,
) -> CreateAppResult[TApp]:
    """
    Do not use this method directly. Instead, use `App[T_app].create()` or `ApplicationBuilder[TApp, TConfig]()`
    """
    return _create_app(config_filename, application_configs, application_modules)


def _create_app(
    config_filename: str = "config.toml",
    # FIXME should be a list of PydanticDataclass
    application_configs: list[type[AbstractConfig]] | None = None,
    application_modules: list[Module | type[Module]] | None = None,
) -> CreateAppResult[TApp]:
    # set up the default configuration as soon as possible
    # also required to call before json_logging.config_root_logger()
    logging.basicConfig(force=True)

    application_builder = (
        ApplicationBuilder[TApp]()
        .with_flask_app_name(environ.get("FLASK_APP", None))
        .with_flask_env(environ.get("FLASK_ENV", None))
        .with_modules(application_modules)
        .use_configuration(
            lambda config_builder: config_builder.enable_ssm(True)
            .with_config_filename(config_filename)
            .with_root_config_type(Config)
            .with_config_types(application_configs)
        )
    )
    app = application_builder.build()
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

    exec_dir = _get_exec_dir()

    connexion_app = FlaskApp(
        config.flask.app_name,
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
            if module_name.endswith("_blueprint") or isinstance(module_var, Blueprint):
                blueprint_modules.append(module_var)

    return blueprint_modules


def _register_blueprint_modules(app: Flask, blueprint_modules: list[Blueprint]):
    for module in blueprint_modules:
        app.register_blueprint(module)
