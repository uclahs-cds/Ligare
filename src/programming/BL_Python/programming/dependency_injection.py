from BL_Python.programming.config import AbstractConfig
from injector import Binder, Module
from typing_extensions import override


class ConfigModule(Module):
    def __init__(
        self, config: AbstractConfig, interface: type[AbstractConfig] = AbstractConfig
    ) -> None:
        super().__init__()
        self._config = config
        self._interface = interface

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(self._interface, to=self._config)
