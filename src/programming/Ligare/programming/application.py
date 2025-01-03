"""
The framework API for creating applications.
"""

import abc
import logging
from collections import defaultdict
from dataclasses import dataclass
from types import FunctionType
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Protocol,
    TypeVar,
    cast,
    final,
    overload,
)

from injector import Binder, Injector, Module
from Ligare.AWS.ssm import SSMParameters
from Ligare.programming.collections.dict import NestedDict
from Ligare.programming.config import (
    AbstractConfig,
    Config,
    ConfigBuilder,
    TConfig,
    load_config,
)
from Ligare.programming.config.exceptions import ConfigBuilderStateError
from Ligare.programming.dependency_injection import ConfigModule
from Ligare.programming.patterns.dependency_injection import (
    BatchModule,
    ConfigurableModule,
    LoggerModule,
)
from Ligare.web.exception import BuilderBuildError, InvalidBuilderStateError
from typing_extensions import Self, override

TAppConfig = TypeVar("TAppConfig", bound=AbstractConfig)


class ApplicationBase(abc.ABC):
    @abc.abstractmethod
    def run(self, *args: Any, **kwargs: Any):
        pass


TApp = TypeVar("TApp", bound=ApplicationBase)


class AppModule(BatchModule, Generic[TApp]):
    def __init__(
        self,
        exec: type[TApp] | Callable[..., TApp] | None = None,
        app_name: str | None = None,
        *args: tuple[Any, Any],
        **kwargs: dict[str, Any],
    ) -> None:
        super().__init__(dict({(arg[0], arg[1]) for arg in args}))
        self._kwargs = kwargs

        if exec is None:
            self._name = app_name if app_name else "app"
            self._exec = None
        else:
            if getattr(exec, "__module__", None) == "builtins":
                raise Exception(
                    "App module type cannot be a builtin like `type`, `object`, etc. It must be a `type[TApp]`."
                )
            self._name = app_name if app_name else exec.__name__
            self._exec = exec

    @override
    def configure(self, binder: Binder) -> None:
        super().configure(binder)

        to: TApp

        if self._exec is not None:
            if isinstance(self._exec, type) and not self._exec == type:
                to = cast(TApp, self._exec(**self._kwargs))
                binder.bind(self._exec, to=to)
            else:
                if isinstance(self._exec, FunctionType):
                    to = self._exec(**self._kwargs)
                    binder.bind(type(to), to=to)
                else:
                    to = cast(TApp, self._exec)
                    binder.bind(type(self._exec), to=to)

            binder.bind(ApplicationBase, to=to)

        binder.install(LoggerModule(self._name))


@dataclass
class CreateAppResult(Generic[TApp]):
    """
    Contains an instantiated `TApp` application in `app`,
    and its associated `Injector` IoC container.

    :param TApp Generic: An instance of the app.
    :param inject Injector: The applications IoC container.
    """

    app: TApp
    injector: Injector

    def run(self):
        return self.injector.call_with_injection(self.app.run)


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
                f"Cannot build the application config without either `{ApplicationConfigBuilder[TConfig].enable_ssm.__name__}` or `{ApplicationConfigBuilder[TConfig].with_config_filename.__name__}` having been configured."
            )

        try:
            config_type = self._config_builder.build()
        except ConfigBuilderStateError as e:
            raise BuilderBuildError(
                f"A root config must be specified using `{ApplicationConfigBuilder[TConfig].with_root_config_type.__name__}`, `{ApplicationConfigBuilder[TConfig].with_config_type.__name__}`, or `{ApplicationConfigBuilder[TConfig].with_config_types.__name__}` before calling `{ApplicationConfigBuilder[TConfig].build.__name__}`."
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


class ApplicationBuilder(Generic[TApp]):
    @overload
    def __init__(self, exec: type[TApp] | Callable[[], TApp]) -> None: ...
    @overload
    def __init__(
        self, exec: type[TApp] | Callable[..., TApp], **kwargs: Any
    ) -> None: ...

    def __init__(self, exec: type[TApp] | Callable[..., TApp], **kwargs: Any) -> None:
        super().__init__()
        self._modules: list[Module | type[Module]] = [AppModule(exec, None, **kwargs)]
        self._config_overrides: dict[str, Any] = {}

    _APPLICATION_CONFIG_BUILDER_PROPERTY_NAME: str = "__application_config_builder"

    @property
    def _application_config_builder(self) -> ApplicationConfigBuilder[AbstractConfig]:
        builder = getattr(
            self, ApplicationBuilder._APPLICATION_CONFIG_BUILDER_PROPERTY_NAME, None
        )

        if builder is None:
            builder = ApplicationConfigBuilder[AbstractConfig]()
            self._application_config_builder = builder.with_root_config_type(Config)

        return builder

    @_application_config_builder.setter
    def _application_config_builder(
        self, value: ApplicationConfigBuilder[AbstractConfig]
    ):
        setattr(
            self, ApplicationBuilder._APPLICATION_CONFIG_BUILDER_PROPERTY_NAME, value
        )

    @overload
    def with_module(self, module: Module) -> Self: ...
    @overload
    def with_module(self, module: type[Module]) -> Self: ...
    def with_module(self, module: Module | type[Module]) -> Self:
        if isinstance(module, AppModule):
            raise Exception(
                "Cannot add a module of type `AppModule`. This module is added when `ApplicationBuilder` is instantiated."
            )

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
        __application_config_builder_callback: ApplicationConfigBuilderCallback[
            AbstractConfig
        ],
    ) -> Self:
        """
        Execute changes to the builder's `ApplicationConfigBuilder[TAppConfig]` instance.

        `__builder_callback` can return `None`, or the instance of `ApplicationConfigBuilder[TAppConfig]` passed to its `config_builder` argument.
        This allowance is so lambdas can be used; `ApplicationBuilder[T_app, TAppConfig]` does not use the return value.
        """
        ...

    @overload
    def use_configuration(
        self, __application_config_builder: ApplicationConfigBuilder[AbstractConfig]
    ) -> Self:
        """Replace the builder's default `ApplicationConfigBuilder[TAppConfig]` instance, or any instance previously assigned."""
        ...

    def use_configuration(
        self,
        application_config_builder: ApplicationConfigBuilderCallback[AbstractConfig]
        | ApplicationConfigBuilder[AbstractConfig],
    ) -> Self:
        if callable(application_config_builder):
            _ = application_config_builder(self._application_config_builder)
        else:
            self._application_config_builder = application_config_builder

        return self

    def _build_config(self) -> AbstractConfig:
        try:
            config = self._application_config_builder.build()
        except InvalidBuilderStateError as e:
            raise BuilderBuildError(
                f"`{ApplicationBuilder[TApp].__name__}` failed to build the application configuration because the `{ApplicationConfigBuilder[AbstractConfig].__name__}` instance was improperly configured. \
Review the exception raised from `{ApplicationConfigBuilder[AbstractConfig].__name__}` and apply fixes through this `{ApplicationBuilder[TApp].__name__}` instance's `{ApplicationBuilder[TApp].use_configuration.__name__}` method."
            ) from e
        except BuilderBuildError as e:
            raise BuilderBuildError(
                f"`{ApplicationBuilder[TApp].__name__}` failed to build the application configuration due to an error when creating the application configuration. \
Review the exception raised from `{ApplicationConfigBuilder[AbstractConfig].__name__}` and apply fixes through this `{ApplicationBuilder[TApp].__name__}` instance's `{ApplicationBuilder[TApp].use_configuration.__name__}` method."
            ) from e

        if config is None:
            raise BuilderBuildError(
                f"The application configuration failed to load for an unknown reason. Review the `{ApplicationConfigBuilder[AbstractConfig].__name__}` instance's configuration."
            )

        return config

    def _register_config_modules(self, config: AbstractConfig):
        config_generator = cast(
            Generator[tuple[str, AbstractConfig], None, None], config
        )
        config_modules = (
            [ConfigModule(config, type(config)) for (_, config) in config_generator]
            + [ConfigModule(config, Config)]
            # Forcefully register the generated config as a module of its own type.
            # This causes the "root" config type to resolve as the generated config
            # without requiring application authors to worry about this.
            # This means applications can use the `Ligare.programming.config.Config`
            # class _or_ whatever the root config type is to get the full config.
            # Because of how the config generation works, there is only one base type.
            + [ConfigModule(config, config.__class__.__bases__[0])]
        )

        _ = self.with_modules(cast(list[Module | type[Module]], config_modules))

    def _build_application_modules(self) -> list[Module | type[Module]]:
        application_modules = self._modules if self._modules else []

        return [
            (module if isinstance(module, Module) else module())
            for module in (application_modules if application_modules else [])
        ]

    def build(self) -> CreateAppResult[TApp]:
        config = self._build_config()

        self._register_config_modules(config)

        modules = self._build_application_modules()

        injector = Injector(modules)

        app = cast(TApp, injector.get(ApplicationBase))
        return CreateAppResult[TApp](app=app, injector=injector)
