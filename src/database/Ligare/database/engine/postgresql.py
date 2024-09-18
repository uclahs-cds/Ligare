from importlib.util import find_spec
from typing import Any, Callable, Union

from Ligare.database.config import DatabaseConnectArgsConfig
from Ligare.database.types import IScopedSessionFactory, MetaBase
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import sessionmaker
from typing_extensions import override


class PostgreSQLScopedSession(
    ScopedSession, IScopedSessionFactory["PostgreSQLScopedSession"]
):
    @override
    @staticmethod
    def create(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, Any] | None = None,
        connect_args: DatabaseConnectArgsConfig | None = None,
        bases: list[MetaBase | type[MetaBase]] | None = None,
    ) -> "PostgreSQLScopedSession":
        if find_spec("psycopg2") is None:
            raise ModuleNotFoundError(
                "No module named 'psycopg2'. Install PostgreSQL support through `Ligare.database[postgres]` or `Ligare.database[postgres-binary]`."
            )

        engine = create_engine(
            connection_string,
            echo=echo,
            execution_options=execution_options or {},
            connect_args=connect_args.model_dump() if connect_args is not None else {},
        )

        if bases:
            PostgreSQLScopedSession._alter_base_schemas(engine, bases)

        return PostgreSQLScopedSession(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )

    @staticmethod
    def _alter_base_schemas(engine: Engine, bases: list[MetaBase | type[MetaBase]]):
        # This renames all tables to undo any renaming that previously happened
        # from, e.g., our SQLite engine.
        for metadata_base in bases:
            metadata_base.metadata.reflect(bind=engine)
            for table_subclass in type(metadata_base).__subclasses__(metadata_base):
                schema: str | None = None
                if hasattr(metadata_base, "__table_args__") and isinstance(
                    metadata_base.__table_args__, dict
                ):
                    schema = metadata_base.__table_args__.get("schema")

                if schema:
                    table_name: list[str] = table_subclass.__tablename__.split(".")
                    # Trim all prepended schema names
                    while table_name[0] == schema:
                        table_name = table_name[1:]

                    table_subclass.__tablename__ = table_name[0]

                    for table in metadata_base.metadata.sorted_tables:
                        table_name = table.name.split(".")
                        while table_name[0] == table.schema:
                            table_name = table_name[1:]

                        table.name = ".".join(table_name)
                        table.fullname = f"{table.schema}.{table.name}"

    def __init__(
        self,
        session_factory: Union[Callable[..., Any], "sessionmaker[Any]"],
        scopefunc: Any = None,
    ) -> None:
        super().__init__(session_factory, scopefunc)
