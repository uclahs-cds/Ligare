from BL_Python.programming.collections.dict import AnyDict
from injector import Binder, CallableProvider, Module, singleton
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import Session
from typing_extensions import override


class ScopedSessionModule(Module):
    """
    Configure SQLAlchemy Session depedencies for Injector.
    """

    def __init__(self, connection_string: str):
        assert (
            connection_string is not None
        ), "Cannot initialize the database module without a valid connection string"
        super().__init__()
        self._connection_string = connection_string

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
        return DatabaseEngine.get_session_from_connection_string(
            self._connection_string, config.SQLALCHEMY_ECHO
        )

    @inject
    def _get_session(self, session_factory: ScopedSession) -> Session:
        """
        Returns a Session instance from the injected ScopedSession instance.
        """
        session: Session = session_factory()
        return session
