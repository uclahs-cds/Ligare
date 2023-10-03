from BL_Python.programming.config import AbstractConfig
from injector import Binder, Module
from typing_extensions import override


class ConfigModule(Module):
    def __init__(self, config: AbstractConfig) -> None:
        super().__init__()
        self._config = config

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(AbstractConfig, to=self._config)
