from injector import Injector
from Ligare.programming.config import AbstractConfig
from Ligare.programming.dependency_injection import ConfigModule
from typing_extensions import override


def test__ConfigModule__injector_binds_Config_module_to_AbstractConfig_by_default():
    class FooConfig(AbstractConfig):
        @override
        def post_load(self) -> None:
            return super().post_load()

    foo_config = FooConfig()
    config_module = ConfigModule(foo_config)
    injector = Injector(config_module)

    assert injector.get(AbstractConfig) == foo_config


def test__ConfigModule__injector_binds_configured_Config_module():
    class FooConfig(AbstractConfig):
        @override
        def post_load(self) -> None:
            return super().post_load()

        x: int = 123

    foo_config = FooConfig()
    foo_config.x = 999

    config_module = ConfigModule(foo_config, FooConfig)
    injector = Injector(config_module)

    assert injector.get(FooConfig) == foo_config
