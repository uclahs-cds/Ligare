"""
The framework API for creating Flask and Connexion applications.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from os import path
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    cast,
    final,
    overload,
)

from connexion import FlaskApp
from connexion.options import SwaggerUIOptions
from flask import Blueprint, Flask
from flask_injector import FlaskInjector
from injector import Injector
from lib_programname import get_path_executed_script
from Ligare.AWS.ssm import SSMParameters
from Ligare.programming.application import ApplicationBase
from Ligare.programming.application import (
    ApplicationBuilder as GenericApplicationBuilder,
)
from Ligare.programming.application import AppModule
from Ligare.programming.collections.dict import NestedDict
from Ligare.programming.config import AbstractConfig, ConfigBuilder, load_config
from Ligare.programming.config.exceptions import ConfigInvalidError
from Ligare.programming.exception import BuilderBuildError, InvalidBuilderStateError
from typing_extensions import Self, override

from .config import Config, FlaskConfig
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
class CreateAppResult(ApplicationBase, Generic[T_app]):
    """
    Contains an instantiated Flask application and its
    associated application "container." This is either
    the same Flask instance, or an OpenAPI application.

    :param flask_app Generic: The Flask application.
    :param app_injector AppInjector[T_app]: The application's wrapper and IoC container.
    """

    flask_app: Flask
    app_injector: AppInjector[T_app]

    @property
    def app(self) -> T_app:
        return self.app_injector.app

    @property
    def injector(self) -> Injector:
        return self.app_injector.flask_injector.injector

    @overload
    def run(self) -> None: ...

    @overload
    def run(
        self: "CreateAppResult[Flask]",
        *,
        host: str | None = None,
        port: int | None = None,
        debug: bool | None = None,
        load_dotenv: bool = True,
        **options: Any,
    ) -> None:
        """
        Call this method to start your application.
        This method is a passthrough for `Flask.run`.

        Reference https://github.com/encode/uvicorn/blob/fe3910083e3990695bc19c2ef671dd447262ae18/uvicorn/main.py#L463

        :param host: The hostname this application should accept requests for.
                              If `None`, the value in the application's `FlaskConfig` instance is used;
                              otherwise, this parameter value is used.
        :param port: The port this application should listen on for requests.
                              If `None`, the value in the application's `FlaskConfig` instance is used;
                              otherwise, this parameter value is used.
        """
        ...

    @overload
    def run(
        self: "CreateAppResult[FlaskApp]",
        *,
        import_string: str | None = None,
        host: str | None = None,
        # uvicorn's default is 8000 but we default to 5000
        # and try to load the value from a config file
        port: int | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Call this method to start your application.
        This method is partly a passthrough for `uvicorn.run`.

        Reference https://github.com/encode/uvicorn/blob/fe3910083e3990695bc19c2ef671dd447262ae18/uvicorn/main.py#L463

        :param import_string: application as import string (eg. "main:app"). This is needed to run
                              using reload.
        :param host: The hostname this application should accept requests for.
                              If `None`, the value in the application's `FlaskConfig` instance is used;
                              otherwise, this parameter value is used.
        :param port: The port this application should listen on for requests.
                              If `None`, the value in the application's `FlaskConfig` instance is used;
                              otherwise, this parameter value is used.
        """
        ...

    @override
    def run(
        self,
        *,
        import_string: str | None = None,
        # uvicorn's default is 127.0.0.1 but we default to localhost
        # and try to load the value from a config file
        host: str | None = None,
        # uvicorn's default is 8000 but we default to 5000
        # and try to load the value from a config file
        port: int | None = None,
        **kwargs: Any,
    ):
        """
        Call this method to start your application.
        This method is partly a passthrough for `uvicorn.run`.

        Reference https://github.com/encode/uvicorn/blob/fe3910083e3990695bc19c2ef671dd447262ae18/uvicorn/main.py#L463

        :param import_string: application as import string (eg. "main:app"). This is needed to run
                              using reload.
        :param host: The hostname this application should accept requests for.
                              If `None`, the value in the application's `FlaskConfig` instance is used;
                              otherwise, this parameter value is used.
        :param port: The port this application should listen on for requests.
                              If `None`, the value in the application's `FlaskConfig` instance is used;
                              otherwise, this parameter value is used.
        """
        app = self.app_injector.app
        injector = self.app_injector.flask_injector.injector
        config = injector.get(FlaskConfig)

        host = host or config.host
        port = port or int(config.port)

        if isinstance(app, FlaskApp):
            app.run(
                import_string=import_string,  # pyright: ignore[reportArgumentType] the connexion type annotation is wrong; `None` is supported.
                host=host,
                port=port,
                **kwargs,
            )
        else:
            app.run(
                host=host,
                port=port,
                **kwargs,
            )


FlaskAppResult = CreateAppResult[Flask]
OpenAPIAppResult = CreateAppResult[FlaskApp]


class UseConfigurationCallback(Protocol[TAppConfig]):
    """
    The callback for configuring an application's configuration.

    :param TAppConfig Protocol: The AbstractConfig type to be configured.
    """

    def __call__(
        self,
        config_builder: ConfigBuilder[TAppConfig],
        config_overrides: dict[str, Any],
    ) -> "None | ConfigBuilder[TAppConfig]":
        """
        Set up parameters for the application's configuration.

        :param ConfigBuilder[TAppConfig] config_builder: The ConfigBuilder instance.
        :param dict[str, Any] config_overrides: A dictionary of key/values that are applied over all keys that might exist in an instantiated config.
        :raises InvalidBuilderStateError: Upon a call to `build()`, the builder is misconfigured.
        :raises BuilderBuildError: Upon a call to `build()`, a failure occurred during the instantiation of the configuration.
        :raises Exception: Upon a call to `build()`, an unknown error occurred.
        :return None | ConfigBuilder[TAppConfig]: The callback may return `None` or the received `ConfigBuilder` instance so as to support the use of lambdas. This return value is not used.
        """


@final
class ApplicationConfigBuilder(Generic[TAppConfig]):
    _DEFAULT_CONFIG_FILENAME: str = "config.toml"

    def __init__(self) -> None:
        self._config_value_overrides: dict[str, Any] = {}
        self._config_builder: ConfigBuilder[TAppConfig] = ConfigBuilder[TAppConfig]()
        self._config_filename: str = ApplicationConfigBuilder._DEFAULT_CONFIG_FILENAME
        self._use_filename: bool = False
        self._use_ssm: bool = False

    def with_config_builder(self, config_builder: ConfigBuilder[TAppConfig]) -> Self:
        self._config_builder = config_builder
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

    def build(self) -> TAppConfig | None:
        _ = self._config_builder.with_root_config(Config)  # pyright: ignore[reportArgumentType]

        if not (self._use_ssm or self._use_filename):
            raise InvalidBuilderStateError(
                f"Cannot build the application config without either `{ApplicationConfigBuilder[TAppConfig].enable_ssm.__name__}` or `{ApplicationConfigBuilder[TAppConfig].with_config_filename.__name__}` having been configured."
            )

        config_type = self._config_builder.build()

        full_config: TAppConfig | None = None
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
    ) -> "None | ApplicationConfigBuilder[TAppConfig]":
        """
        A method used to configure an `ApplicationConfigBuilder`.
        Call the builder methods on `config_builder` to set the
        desired options.

        **Do not call `build()`** as it is called by the `ApplicationBuilder`.

        :param ApplicationConfigBuilder[TAppConfig] config_builder:
        :return None | ApplicationConfigBuilder[TAppConfig]: Any return value is ignored.
        """
        ...


@final
class ApplicationBuilder(GenericApplicationBuilder[T_app]):
    def __init__(
        self,
        exec: type[T_app] | Callable[..., T_app],
    ) -> None:
        super().__init__(exec=exec)

    def with_flask_app_name(self, value: str | None) -> Self:
        self._config_overrides["app_name"] = value
        return self

    def with_flask_env(self, value: str | None) -> Self:
        self._config_overrides["env"] = value
        return self

    @override
    def use_configuration(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        __application_config_builder_callback: ApplicationConfigBuilderCallback[Config],
    ) -> Self:
        """
        Execute changes to the builder's `ApplicationConfigBuilder[TAppConfig]` instance.

        `__builder_callback` can return `None`, or the instance of `ApplicationConfigBuilder[TAppConfig]` passed to its `config_builder` argument.
        This allowance is so lambdas can be used; `ApplicationBuilder[T_app, TAppConfig]` does not use the return value.
        """
        super().use_configuration(__application_config_builder_callback)  # pyright: ignore[reportCallIssue,reportArgumentType]
        return self

    @override
    def build(self) -> CreateAppResult[T_app]:
        config_overrides = cast(NestedDict[str, Any], defaultdict(dict))

        if (
            override_app_name := self._config_overrides.get("app_name", None)
        ) is not None and override_app_name != "":
            config_overrides["flask"]["app_name"] = override_app_name

        if (
            override_env := self._config_overrides.get("env", None)
        ) is not None and override_env != "":
            config_overrides["flask"]["env"] = override_env

        _ = self._application_config_builder.with_root_config_type(
            Config
        ).with_config_value_overrides(config_overrides)

        config = cast(Config, self._build_config())
        self._register_config_modules(config)

        if config.flask is None:
            raise ConfigInvalidError(
                "You must set [flask] in the application configuration. Review the documentation for the Ligare.web TOML format and requirements."
            )

        if not config.flask.app_name:
            raise ConfigInvalidError(
                "You must set the Flask application name in the [flask.app_name] config or FLASK_APP envvar. Review the documentation for the Ligare.web TOML format and requirements."
            )

        if not self._app_module_set:
            _ = self.with_module(
                AppModule(self._exec, None, import_name=config.flask.app_name)
            )

        if config.flask.openapi is not None:
            openapi = configure_openapi(config)
            app = cast(T_app, openapi)
        else:
            app = cast(T_app, configure_blueprint_routes(config))

        register_error_handlers(app)
        _ = register_api_request_handlers(app)
        _ = register_api_response_handlers(app)
        _ = register_context_middleware(app)

        modules = self._build_application_modules()

        flask_injector = configure_dependencies(app, application_modules=modules)

        flask_app = app.app if isinstance(app, FlaskApp) else app
        return CreateAppResult[T_app](
            flask_app, AppInjector[T_app](app, flask_injector)
        )


def _override_connexion_spec_clone():
    import copy

    from connexion.spec import Specification

    def clone(self: Specification):
        return type(self)(copy.deepcopy(cast(dict[Any, Any], self._raw_spec)))  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]

    Specification.clone = clone


def configure_openapi(config: Config, name: Optional[str] = None):
    """
    Instantiate Connexion and set Flask logging options
    """

    _override_connexion_spec_clone()

    if (
        config.flask is None
        or config.flask.openapi is None
        or config.flask.openapi.spec_path is None
    ):
        raise Exception(
            "OpenAPI configuration is empty. Review the `openapi` section of your application's `config.toml`."
        )

    if config.flask.openapi.use_swagger and config.flask.openapi.swagger_url in [
        "/",
        "",
    ]:
        raise Exception(
            f'The configured Swagger URL "{config.flask.openapi.swagger_url}" cannot be used. Remove `flask.openapi.swagger_url` from your configuration, or change the value to something else.'
        )

    exec_dir = _get_exec_dir()

    connexion_app = FlaskApp(
        config.flask.app_name,
        specification_dir=exec_dir,
        swagger_ui_options=SwaggerUIOptions(
            swagger_ui=config.flask.openapi.use_swagger,
            swagger_ui_path=config.flask.openapi.swagger_url
            or SwaggerUIOptions.swagger_ui_path,
        ),
    )
    app = connexion_app.app
    config.update_flask_config(app.config)

    _ = connexion_app.add_api(
        f"{config.flask.app_name}/{config.flask.openapi.spec_path}",
        validate_responses=config.flask.openapi.validate_responses,
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
