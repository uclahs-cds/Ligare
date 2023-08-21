from typing import Any, Tuple

from BL_Python.programming.patterns.dependency_injection import LoggerModule, Module
from flask import Config as Config
from flask import Flask
from injector import Binder
from typing_extensions import override


class AppModule(Module):
    def __init__(self, flask_app: Flask, *args: Any) -> None:
        super().__init__()
        self._flask_app = flask_app
        self._other_dependencies = args

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(Flask, to=self._flask_app)
        binder.bind(Config, to=self._flask_app.config)
        binder.install(LoggerModule(self._flask_app.name))

        for dependency in self._other_dependencies:
            binder.bind(type(dependency), to=dependency)
