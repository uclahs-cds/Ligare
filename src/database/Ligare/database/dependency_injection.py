from injector import Binder, CallableProvider, Injector, inject, singleton
from Ligare.database.config import Config, DatabaseConfig
from Ligare.database.engine import DatabaseEngine
from Ligare.database.types import MetaBase
from Ligare.programming.config import AbstractConfig
from Ligare.programming.dependency_injection import ConfigModule
from Ligare.programming.patterns.dependency_injection import ConfigurableModule
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import Session
from typing_extensions import override

from .config import DatabaseConfig


class ScopedSessionModule(ConfigurableModule):
    """
    Configure SQLAlchemy Session depedencies for Injector.
    """

    @override
    @staticmethod
    def get_config_type() -> type[AbstractConfig]:
        return DatabaseConfig

    _bases: list[MetaBase | type[MetaBase]] | None = None

    @override
    def configure(self, binder: Binder) -> None:
        # Any ScopedSession dependency should be the same for the lifetime of the application.
        # ScopeSession is a factory that creates a Session per thread.
        # The Session returned is the same for the lifetime of the thread.
        binder.bind(
            ScopedSession,
            to=CallableProvider(self._get_scoped_session),
            scope=singleton,
        )

        # Injecting a Session means calling the ScopedSession factory.
        # This is largely a convenience dependency, because the same
        # instance can be obtained by executing the factory that is
        # ScopedSession. ScopedSession handles all thread local concerns.
        # It is safe for this method to be called multiple times.
        binder.bind(Session, to=CallableProvider(self._get_session))

    def __init__(self, bases: list[MetaBase | type[MetaBase]] | None = None) -> None:
        super().__init__()
        self._bases = bases

    @inject
    def _get_scoped_session(self, database_config: DatabaseConfig) -> ScopedSession:
        """
        Returns a ScopedSession instance configured with
        the correct engine and connection string.
        Defaults to using the `sessionmaker` Session factory.
        """
        return DatabaseEngine.get_session_from_connection_string(
            database_config.connection_string,
            database_config.sqlalchemy_echo,
            {},
            database_config.connect_args,
            bases=self._bases,
        )

    @inject
    def _get_session(self, session_factory: ScopedSession) -> Session:
        """
        Returns a Session instance from the injected ScopedSession instance.
        """
        session: Session = session_factory()
        return session


def get_database_config_container(config: Config):
    config_module = ConfigModule(config, Config)
    database_config_module = ConfigModule(config.database, DatabaseConfig)

    return Injector([config_module, database_config_module])


def get_database_ioc_container(
    config: Config, bases: list[MetaBase | type[MetaBase]] | None = None
):
    container = get_database_config_container(config)
    container.binder.install(ScopedSessionModule(bases=bases))
    return container
