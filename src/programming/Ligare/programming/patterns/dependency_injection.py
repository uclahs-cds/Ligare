"""
`Injector <https://pypi.org/project/injector/>`_ dependency injection modules for extension by other modules.
"""

import json
import logging
import sys
from typing import Any, Callable, TypeVar

from injector import Binder, Module, Provider
from Ligare.programming.config import AbstractConfig
from typing_extensions import override


class LoggerModule(Module):
    def __init__(
        self,
        name: str | None = None,
        log_level: int | str = logging.INFO,
        log_to_stdout: bool = False,
    ) -> None:
        super().__init__()

        if isinstance(log_level, str):
            level = getattr(logging, log_level, logging.DEBUG)
        else:
            level = log_level

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        if log_to_stdout:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            self._logger.addHandler(handler)

    @override
    def configure(self, binder: Binder) -> None:
        binder.bind(logging.Logger, to=self._logger)


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    https://stackoverflow.com/a/70223539

    @param dict fmt_dict: Key: logging format attribute pairs. Defaults to {"message": "message"}.
    @param str time_format: time.strftime() format string. Default: "%Y-%m-%dT%H:%M:%S"
    @param str msec_format: Microsecond formatting. Appended at the end. Default: "%s.%03dZ"
    """

    @override
    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        fmt_dict: dict[str, str] | None = None,
        time_format: str = "%Y-%m-%dT%H:%M:%S",
        msec_format: str = "%s.%03dZ",
    ):
        self.fmt_dict: dict[str, str] = (
            fmt_dict if fmt_dict is not None else {"message": "message"}
        )
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    @override
    def usesTime(self) -> bool:
        """
        Overwritten to look for the attribute in the format dict values instead of the fmt string.
        """
        return "asctime" in self.fmt_dict.values()

    @override
    def formatMessage(self, record: logging.LogRecord) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Overwritten to return a dictionary of the relevant LogRecord attributes instead of a string.
        KeyError is raised if an unknown attribute is provided in the fmt_dict.
        """
        return {
            fmt_key: record.__dict__.get(fmt_val, None)
            for fmt_key, fmt_val in self.fmt_dict.items()
        }

    @override
    def format(self, record: logging.LogRecord) -> str:
        """
        Mostly the same as the parent's class method, the difference being that a dict is manipulated and dumped as JSON
        instead of a string.
        """
        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        message_dict = self.formatMessage(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(message_dict, default=str)


class JSONLoggerModule(LoggerModule):
    """
    Force all loggers to use a StreamHandler that outputs JSON
    """

    def __init__(
        self,
        name: str | None = None,
        log_level: int | str = logging.INFO,
        log_to_stdout: bool = False,
        formatter: JSONFormatter | None = None,
    ) -> None:
        super().__init__(name, log_level, log_to_stdout)

        if not formatter:
            formatter = JSONFormatter({
                "level": "levelname",
                "message": "message",
                "file": "pathname",
                "func": "funcName",
                "line": "lineno",
                "loggerName": "name",
                "processName": "processName",
                "processID": "process",
                "threadName": "threadName",
                "threadID": "thread",
                "timestamp": "asctime",
            })

        json_handler = logging.StreamHandler()
        json_handler.formatter = formatter
        if logging.lastResort is None:
            logging.lastResort = json_handler
        else:
            logging.lastResort.setFormatter(formatter)

        original_getLogger = logging.getLogger

        def force_json_format(*args: Any, **kwargs: Any):
            logger = original_getLogger(*args, **kwargs)

            original_addHandler = logger.addHandler
            if hasattr(original_addHandler, "__overridden__"):
                return logger

            def addHandler(hdlr: logging.Handler):
                hdlr.setFormatter(formatter)
                return original_addHandler(hdlr)

            setattr(addHandler, "__overridden__", True)

            logger.addHandler = addHandler
            return logger

        logging.getLogger = force_json_format

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
