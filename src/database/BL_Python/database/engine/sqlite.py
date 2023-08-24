from typing import Any, Callable

from sqlalchemy import create_engine, event
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import sessionmaker


class SQLiteScopedSession(ScopedSession):
    @staticmethod
    def create(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, Any] | None = None,
    ):
        """
        Create a new session factory for SQLite.
        """
        engine = create_engine(
            connection_string, echo=echo, execution_options=execution_options or {}
        )

        return SQLiteScopedSession(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )

    def __init__(
        self,
        session_factory: Callable[..., Any] | "sessionmaker[Any]",
        scopefunc: Any = None,
    ) -> None:
        super().__init__(session_factory, scopefunc)
        """
        This callback is used to subscribe to the "connect" core SQLAlchemy event.
        When a session is instantiated from sessionmaker, and immediately after a connection
        is made to the database, this will issue the `pragma foreign_key=ON` query. This
        query ensures SQLite respects foreign key constraints.
        This will be removed at a later date.
        """

        def _fk_pragma_on_connect(dbapi_con: Any, con_record: Any):
            """
            Called immediately after a connection is established.
            """
            dbapi_con.execute("pragma foreign_keys=ON")

        event.listen(self.bind, "connect", _fk_pragma_on_connect)
