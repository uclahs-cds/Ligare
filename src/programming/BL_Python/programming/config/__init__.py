import abc
from pathlib import Path
from typing import Any, Generic, TypeVar, cast

import toml
from BL_Python.programming.collections.dict import AnyDict, merge
from BL_Python.programming.config.exceptions import (
    ConfigBuilderStateError,
    NotEndsWithConfigError,
)

TConfig = TypeVar("TConfig")


class AbstractConfig(abc.ABC):
    pass


class ConfigBuilder(Generic[TConfig]):
    _root_config: type[TConfig] | None = None
    _configs: list[type[AbstractConfig]] | None = None

    def with_root_config(self, config: "type[TConfig]"):
        self._root_config = config
        return self

    def with_configs(self, configs: list[type[AbstractConfig]]):
        self._configs = configs
        return self

    def build(self) -> type[TConfig]:
        if self._root_config and not self._configs:
            return self._root_config

        if not self._configs:
            raise ConfigBuilderStateError(
                "Cannot build a config without any base config types specified."
            )

        _new_type_base = self._root_config if self._root_config else object

        attrs: dict[Any, Any] = {}
        annotations: dict[str, Any] = {}

        for config in self._configs:
            if not config.__name__.endswith("Config"):
                raise NotEndsWithConfigError(
                    f"Class name '{config.__name__}' is not a valid config class. The name must end with 'Config'"
                )

            config_name = config.__name__[: config.__name__.rindex("Config")].lower()
            annotations[config_name] = config
            attrs[config_name] = None

        attrs["__annotations__"] = annotations
        # make one type that has the names of the config objects
        # as attributes, and the class as their type
        _new_type = cast(
            "type[TConfig]", type("GeneratedConfig", (_new_type_base,), attrs)
        )

        return _new_type


def load_config(
    config_type: type[TConfig],
    toml_file_path: str | Path,
    config_overrides: AnyDict | None = None,
) -> TConfig:
    config_dict: dict[str, Any] = toml.load(toml_file_path)

    if config_overrides is not None:
        config_dict = merge(config_dict, config_overrides)

    config = config_type(**config_dict)
    return config
