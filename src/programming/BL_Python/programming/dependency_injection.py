from injector import Binder, Module
from typing_extensions import override

from .config import Config


class ConfigModule(Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(Config, to=self._config)
