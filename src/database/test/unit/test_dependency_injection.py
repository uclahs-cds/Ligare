from typing import cast

from BL_Python.database.config import DatabaseConfig
from BL_Python.database.dependency_injection import ScopedSessionModule
from BL_Python.programming.dependency_injection import ConfigModule
from injector import Injector
from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import Session


def test__ScopedSessionModule__injector_binds_configured_DatabaseConfig_module():
    database_config = DatabaseConfig(
        connection_string="sqlite:///:memory:?test=test", sqlalchemy_echo=True
    )
    config_module = ConfigModule(
        database_config,
        DatabaseConfig,
    )

    injector = Injector([config_module, ScopedSessionModule()])

    assert injector.get(DatabaseConfig) == database_config


def test__ScopedSessionModule__injector_binds_configured_DatabaseConfig_module_from_parent_injector():
    database_config = DatabaseConfig(
        connection_string="sqlite:///:memory:?test=test", sqlalchemy_echo=True
    )
    config_module = ConfigModule(
        database_config,
        DatabaseConfig,
    )
    database_injector = Injector(config_module)

    injector = Injector(ScopedSessionModule(), parent=database_injector)

    assert injector.get(DatabaseConfig) == database_config


def test__ScopedSessionModule__injector_binds_Session_using_configured_DatabaseConfig_module():
    database_config = DatabaseConfig(
        connection_string="sqlite:///:memory:?test=test", sqlalchemy_echo=True
    )
    config_module = ConfigModule(
        database_config,
        DatabaseConfig,
    )

    injector = Injector([config_module, ScopedSessionModule()])

    session = injector.get(Session)
    assert session.bind is not None
    assert str(session.bind.engine.url) == database_config.connection_string
