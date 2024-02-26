import logging
from logging import Logger

from BL_Python.programming.patterns.dependency_injection import LoggerModule
from BL_Python.programming.str import get_random_str
from injector import Injector
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
