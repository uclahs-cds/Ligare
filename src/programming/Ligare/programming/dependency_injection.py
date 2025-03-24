"""
`Injector <https://pypi.org/project/injector/>`_ dependency injection modules for :ref:`Ligare.programming.config`.
"""

from injector import Binder, Module
from Ligare.programming.config import AbstractConfig
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
