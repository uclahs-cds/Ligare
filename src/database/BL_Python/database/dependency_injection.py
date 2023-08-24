from typing import cast

from BL_Python.database.engine import DatabaseEngine
from BL_Python.programming.config import Config
from injector import Binder, CallableProvider, Module, inject, singleton
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import Session
from typing_extensions import override

from .config import DatabaseConfig


class ScopedSessionModule(Module):
    """
    Configure SQLAlchemy Session depedencies for Injector.
    """

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

    @inject
    def _get_scoped_session(self, config: Config) -> ScopedSession:
        """
        Returns a ScopedSession instance configured with
        the correct engine and connection string.
        Defaults to using the `sessionmaker` Session factory.
        """
        database_config: DatabaseConfig
        if isinstance(config, DatabaseConfig):
            database_config = config
        else:
            database_config = cast(DatabaseConfig, config.database)
        return DatabaseEngine.get_session_from_connection_string(
            database_config.connection_string, database_config.sqlalchemy_echo
        )

    @inject
    def _get_session(self, session_factory: ScopedSession) -> Session:
        """
        Returns a Session instance from the injected ScopedSession instance.
        """
        session: Session = session_factory()
        return session
