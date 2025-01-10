"""
`Injector <https://pypi.org/project/injector/>`_ dependency injection modules for extension by other modules.
"""

import logging
import sys
from typing import Callable, TypeVar

from injector import Binder, Module, Provider
from Ligare.programming.config import AbstractConfig
from typing_extensions import override


# FIXME move somewhere else?
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


T = TypeVar("T")


class BatchModule(Module):
    def __init__(
        self, registrations: dict[type[T], None | T | Callable[..., T] | Provider[T]]
    ) -> None:
        super().__init__()
        self._registrations = registrations

    @override
    def configure(self, binder: Binder) -> None:
        for interface, to in self._registrations.items():
            binder.bind(interface, to)


from abc import ABC, abstractmethod


class ConfigurableModule(Module, ABC):
    @staticmethod
    @abstractmethod
    def get_config_type() -> type[AbstractConfig]: ...
