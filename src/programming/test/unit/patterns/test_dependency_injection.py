import logging
from dataclasses import dataclass
from logging import Logger

from injector import Injector
from Ligare.programming.patterns.dependency_injection import BatchModule, LoggerModule
from Ligare.programming.str import get_random_str
from pytest import LogCaptureFixture


def test__LoggerModule__binds_named_Logger():
    logger_name = f"{test__LoggerModule__binds_named_Logger.__name__}-logger"
    logger_module = LoggerModule(logger_name)
    injector = Injector(logger_module)

    logger = logging.getLogger(logger_name)

    assert injector.get(Logger) == logger


def test__LoggerModule__correctly_configures_STDOUT_log_handler(
    caplog: LogCaptureFixture,
):
    logger_name = (
        f"{test__LoggerModule__correctly_configures_STDOUT_log_handler.__name__}-logger"
    )
    logger_module = LoggerModule(logger_name, log_to_stdout=True)
    injector = Injector(logger_module)
    logger = injector.get(Logger)

    random_str = get_random_str(k=26)
    logger.info(random_str)

    assert random_str in {record.msg for record in caplog.records}


def test__BatchModule__binds_multiple_types():
    @dataclass
    class Foo:
        x: int = 123

    @dataclass
    class Bar:
        x: str = "456"

    class Baz:
        x: str = "abc"

        def __init__(self, x: str) -> None:  # pyright: ignore[reportMissingSuperCall]
            self.x = x

    registrations = {Foo: Foo(x=999), Bar: Bar(x="999"), Baz: Baz(x="ABC")}
    batch_module = BatchModule(registrations)  # pyright: ignore[reportArgumentType]
    injector = Injector(batch_module)

    assert injector.get(Foo) == registrations[Foo]
    assert injector.get(Bar) == registrations[Bar]
    assert injector.get(Baz) == registrations[Baz]
