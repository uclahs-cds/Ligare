import logging
import sys
from typing import Any

from injector import Binder, Module
from typing_extensions import override


class LoggerModule(Module):
    def __init__(
        self,
        name: str | None = None,
        log_level: int = logging.INFO,
        log_to_stdout: bool = False,
    ) -> None:
        super().__init__()
        self._logger = logging.getLogger(name)
        self._logger.setLevel(log_level)
        if log_to_stdout:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(log_level)
            self._logger.addHandler(handler)

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(logging.Logger, to=self._logger)


class BatchModule(Module):
    def __init__(self, registrations: dict[Any, Any]) -> None:
        super().__init__()
        self._registrations = registrations

    @override
    def configure(self, binder: Binder) -> None:
        for interface, to in self._registrations.items():
            binder.bind(interface, to)
