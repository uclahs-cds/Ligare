from injector import Binder, Module
from pydantic import BaseModel
from typing_extensions import override


class ConfigModule(Module):
    def __init__(self, config: BaseModel) -> None:
        super().__init__()
        self._config = config

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(BaseModel, to=self._config)
