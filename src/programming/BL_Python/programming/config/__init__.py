import typing
from typing import Any, Type, TypeVar

import toml
from BL_Python.programming.collections.dict import AnyDict, merge
from pydantic.dataclasses import dataclass


# isort: off
# fmt: off
# Fix this error
# https://bugs.python.org/issue45524
# https://github.com/Fatal1ty/mashumaro/issues/28
# Unfortunately Pydantic hides the PydanticDataclass
# behind `if TYPE_CHECKING`, which causes Python
# annotation inspection to fail with methods
# like, e.g. `get_type_hints`.
import pydantic._internal._dataclasses  # import PydanticDataclass
class PydanticDataclass:
    pass
pydantic._internal._dataclasses.PydanticDataclass = PydanticDataclass
# fmt: on
# isort: on
class Config:
    pass


class ConfigBuilder:
    _root_config: Type[Any] | None = None
    _configs: list[Type[Any]] | None = None

    def with_root_config(self, config: Type[PydanticDataclass]):
        self._root_config = config
        return self

    def with_configs(self, configs: list[Type[PydanticDataclass]]):
        self._configs = configs
        return self

    def build(self):
        if self._root_config and not self._configs:
            return self._root_config

        if not self._configs:
            raise Exception("Cannot build a config without any configs.")

        _new_type_base = self._root_config if self._root_config else object

        attrs = {}
        annotations: dict[str, Any] = {}

        for config in self._configs:
            try:
                config_name = config.__name__[
                    : config.__name__.rindex("Config")
                ].lower()
                annotations[config_name] = config
                attrs[config_name] = None
            except ValueError as e:
                raise ValueError(
                    f"Class name '{config.__name__}' is not a valid config class. The name must end with 'Config'"
                ) from e

        attrs["__annotations__"] = annotations
        # make one type that has the names of the config objects
        # as attributes, and the class as their type
        _new_type: Type[Any] = type("GeneratedConfig", (_new_type_base,), attrs)

        return dataclass(frozen=True)(_new_type)


TConfig = TypeVar("TConfig")


def load_config(
    toml_file_path: str,
    config_overrides: AnyDict | None = None,
    config_type: Type[TConfig] = Config,
) -> TConfig:
    config_dict: dict[str, Any] = toml.load(toml_file_path)

    if config_overrides is not None:
        config_dict = merge(config_dict, config_overrides)

    config = config_type(**config_dict)
    return config
