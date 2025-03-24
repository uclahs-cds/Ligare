"""
:ref:`Ligare.programming`'s API for working with configuration files.
=====================================================================
"""

import abc
from pathlib import Path
from typing import Any, Generic, TypeVar, cast

import toml
from Ligare.programming.collections.dict import AnyDict, merge
from Ligare.programming.config.exceptions import (
    ConfigBuilderStateError,
    ConfigInvalidError,
    NotEndsWithConfigError,
)
from pydantic import BaseModel, create_model
from typing_extensions import Self, override


class AbstractConfig(BaseModel, abc.ABC):
    """
    The base type for all pluggable config types.
    """

    @abc.abstractmethod
    def post_load(self) -> None:
        """
        This method is called by `load_config` after TOML data has been loaded into the pluggable config type instance.
        """


class Config(AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()


TConfig = TypeVar("TConfig", bound=AbstractConfig)

from collections import deque


class ConfigBuilder(Generic[TConfig]):
    _root_config: type[TConfig] | None = None
    _configs: deque[type[AbstractConfig]] | None = None

    def with_root_config(self, config_type: type[TConfig]) -> Self:
        """
        Set `config_type` as the "root" config, used during build.

        :param type[TConfig] config_type:
        :return Self:
        """
        self._root_config = config_type
        return self

    def with_configs(self, configs: list[type[AbstractConfig]] | None) -> Self:
        """
        Add a list of pluggable config types that are added to the root TConfig type during build.

        :param list[type[AbstractConfig]] | None configs:
        :return Self:
        """
        if configs is None:
            return self

        if self._configs is None:
            self._configs = deque(configs)
        else:
            self._configs.extend(configs)

        return self

    def with_config(self, config_type: type[AbstractConfig]) -> Self:
        """
        Add a pluggable config type that is added to the root TConfig type during build.

        :param type[AbstractConfig] config_type:
        :return Self:
        """
        if self._configs is None:
            self._configs = deque()

        self._configs.append(config_type)
        return self

    def build(self) -> type[TConfig]:
        """
        Create a TConfig type from the provided build options.

        At least one "root" config, or one pluggable config must be added.
        If a "root" config is not added, the first pluggable config added is used as the root config.

        :raises ConfigBuilderStateError: Raised when the Builder is misconfigured
        :raises NotEndsWithConfigError: Raised when a pluggable config type's name does not end with `Config`
        :return type[TConfig]: The TConfig type, including any pluggable config types
        """
        if self._root_config and not self._configs:
            _new_type = cast(
                "type[TConfig]", type("GeneratedConfig", (self._root_config,), {})
            )
            return _new_type

        if not self._configs:
            raise ConfigBuilderStateError(
                "Cannot build a config without any base config types specified."
            )

        def test_type_name(config_type: type[AbstractConfig]):
            if not config_type.__name__.endswith("Config"):
                raise NotEndsWithConfigError(
                    f"Class name '{config_type.__name__}' is not a valid config class. The name must end with 'Config'"
                )

        _new_type_base = (
            self._root_config if self._root_config else self._configs.popleft()
        )

        test_type_name(_new_type_base)

        annotations: dict[str, Any] = {}

        for config in self._configs:
            test_type_name(config)

            config_name = config.__name__[: config.__name__.rindex("Config")].lower()
            annotations[config_name] = (config, None)

        # make one type that has the names of the config objects
        # as attributes, and the class as their type
        generated_model = create_model(
            "GeneratedConfig",
            __base__=_new_type_base,
            **annotations,
        )

        return cast(type[TConfig], generated_model)


def load_config(
    config_type: type[TConfig],
    toml_file_path: str | Path,
    config_overrides: AnyDict | None = None,
) -> TConfig:
    """
    Load configuration data from a TOML file into a TConfig object instance

    `config_type.post_load` is called on the root config type _only_.

    :param type[TConfig] config_type: The configuration type that is instantiated and hydrated with data from the TOML file.
    :param str | Path toml_file_path: The path to the TOML file to load.
    :param AnyDict | None config_overrides: Explicit data used to override any data in the TOML file, defaults to None
    :return TConfig: The hydrated configuration object
    """
    try:
        config_dict: dict[str, Any] = toml.load(toml_file_path)
    except FileNotFoundError as e:
        full_path = Path(toml_file_path).resolve()
        raise ConfigInvalidError(
            f"The configuration file specified, `{toml_file_path}`, could not be found at `{full_path}` and was not loaded. \
Is the file path correct?"
        ) from e

    if config_overrides is not None:
        config_dict = merge(config_dict, config_overrides)

    config = config_type(**config_dict)

    config.post_load()

    return config
