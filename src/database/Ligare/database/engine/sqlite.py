from sqlite3 import Connection
from typing import Any, Callable

from Ligare.database.config import DatabaseConnectArgsConfig
from Ligare.database.types import IScopedSessionFactory, MetaBase
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.pool import Pool, StaticPool
from sqlalchemy.pool.base import (
    _ConnectionRecord,  # pyright: ignore[reportPrivateUsage]
)
from typing_extensions import override


class SQLiteScopedSession(ScopedSession, IScopedSessionFactory["SQLiteScopedSession"]):
    @override
    @staticmethod
    def create(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, Any] | None = None,
        connect_args: DatabaseConnectArgsConfig | None = None,
        bases: list[MetaBase | type[MetaBase]] | None = None,
    ) -> "SQLiteScopedSession":
        """
        Create a new session factory for SQLite.
        """
        poolclass: type[Pool] | None = None
        # if the connection string is an SQLite in-memory database
        # then make SQLAlchemy maintain a static pool of "connections"
        # so that the in-memory database is not deallocated. Otherwise,
        # the database would disappear when a thread is done with it.
        # Note: SQLite will reject usage from other threads unless
        # the connection string also contains `?check_same_thread=False`,
        # e.g. `sqlite:///:memory:?check_same_thread=False`
        if ":memory:" in connection_string:
            poolclass = StaticPool

        if not execution_options:  # pragma: nocover
            execution_options = {}

        if bases:
            schema_translate_map = {
                base.__table_args__.get("schema"): None
                for base in bases
                if hasattr(base, "__table_args__")
                and isinstance(base.__table_args__, dict)
                and base.__table_args__.get("schema")
            }

            if schema_translate_map:
                execution_options["schema_translate_map"] = schema_translate_map

        engine = create_engine(
            connection_string,
            echo=echo,
            execution_options=execution_options,
            connect_args=connect_args.model_dump() if connect_args is not None else {},
            poolclass=poolclass,
        )

        if bases:
            SQLiteScopedSession._alter_base_schemas(engine, bases)

        return SQLiteScopedSession(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )

    @staticmethod
    def _alter_base_schemas(engine: Engine, bases: list[MetaBase | type[MetaBase]]):
        # SQLite does not have schemas, which are mapped to None above,
        # however, we can "fake" it by querying table names with periods,
        # e.g., `SELECT * FROM 'foo.table'`.
        # This renames all tables to include the schema name in their name.
        for metadata_base in bases:
            metadata_base.metadata.reflect(bind=engine)
            for table_subclass in type(metadata_base).__subclasses__(metadata_base):
                schema: str | None = None
                if hasattr(metadata_base, "__table_args__") and isinstance(
                    metadata_base.__table_args__, dict
                ):
                    schema = metadata_base.__table_args__.get("schema")

                if schema:
                    table_name: str = table_subclass.__tablename__
                    # If the table has already been renamed, skip it.
                    if table_name.split(".")[0] == schema:
                        continue

                    # The type member name needs to be changed to support
                    # constructs like insert(Assay).
                    table_subclass.__tablename__ = f"{schema}.{table_name}"

            for table in metadata_base.metadata.sorted_tables:
                # If the table has already been renamed, skip it.
                if not table.schema or table.name.split(".")[0] == table.schema:
                    continue

                # The metadata name needs to be changed to support most constructs
                table.name = f"{table.schema}.{table.name}"
                table.fullname = f"{table.schema}.{table.schema}.{table.name}"

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

        def _fk_pragma_on_connect(dbapi_con: Connection, con_record: _ConnectionRecord):
            """
            Called immediately after a connection is established.
            """
            _ = dbapi_con.execute("pragma foreign_keys=ON")

        event.listen(self.bind, "connect", _fk_pragma_on_connect)
