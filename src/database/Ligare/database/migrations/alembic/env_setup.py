from dataclasses import dataclass
from functools import lru_cache
from logging.config import fileConfig
from typing import Any, List, Literal, Protocol, cast, final

from alembic import context
from injector import inject
from Ligare.database.config import DatabaseConfig
from Ligare.database.schema.postgresql import PostgreSQLDialect
from Ligare.database.schema.sqlite import SQLiteDialect
from Ligare.database.types import MetaBase

# TODO only do this when using PostgreSQL,
# and detect if the module is installed
# so we can show a helpful error message
try:
    from psycopg2.errors import UndefinedTable  # pyright: ignore[reportAssignmentType]
except ImportError:

    class UndefinedTable:
        pass


from sqlalchemy import MetaData, Table, engine_from_config, pool
from sqlalchemy.engine import Connectable, Connection, Engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.schema import SchemaItem


class type_include_object(Protocol):
    def __call__(
        self,
        object: SchemaItem,
        name: str | None,
        type_: Literal[
            "schema",
            "table",
            "column",
            "index",
            "unique_constraint",
            "foreign_key_constraint",
        ],
        reflected: bool,
        compare_to: SchemaItem | None,
    ) -> bool: ...


class type_include_schemas(Protocol):
    def __call__(self, names: List[str]) -> type_include_object: ...


@dataclass
class type_metadata:
    include_schemas: type_include_schemas
    target_metadata: List[MetaData]
    schemas: List[str]


@final
class AlembicEnvSetup:
    _config: DatabaseConfig

    @inject
    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config

    @lru_cache(maxsize=1)
    def get_config(self):
        # this is the Alembic Config object, which provides
        # access to the values within the .ini file in use.
        config = context.config

        # Interpret the config file for Python logging.
        # This line sets up loggers basically.
        if config.config_file_name is not None:
            # raise Exception("Config file is missing.")
            fileConfig(config.config_file_name)

        # FIXME why is this here?
        config.set_main_option("sqlalchemy.url", self._config.connection_string)

        return config

    _type_metadata: type_metadata | None = None

    def get_metadata(self, bases: list[MetaBase]):
        if self._type_metadata is not None:
            return self._type_metadata

        def include_schemas(names: List[str]):
            def include_object(
                object: SchemaItem | Table,
                name: str | None,
                type_: Literal[
                    "schema",
                    "table",
                    "column",
                    "index",
                    "unique_constraint",
                    "foreign_key_constraint",
                ],
                reflected: bool,
                compare_to: SchemaItem | None,
            ) -> bool:
                if type_ == "table" and isinstance(object, Table):
                    return object.schema in names
                return True

            return include_object

        target_metadata = [base.metadata for base in bases]
        schemas = [
            base.__table_args__["schema"]
            for base in bases
            if hasattr(base, "__table_args__")
            and isinstance(base.__table_args__, dict)
            and base.__table_args__["schema"] is not None
        ]

        self._type_metadata = type_metadata(include_schemas, target_metadata, schemas)
        return self._type_metadata

    def _configure_context(
        self, bases: list[MetaBase], connection: Connection | Connectable | Engine
    ):
        metadata = self.get_metadata(bases)
        target_metadata = metadata.target_metadata
        include_schemas = metadata.include_schemas
        schemas = metadata.schemas

        if connection.engine is None:
            raise Exception("Unknown error. Connection engine is not set.")

        if not isinstance(connection, Connection):
            raise Exception(
                f"Unknown error. Connection is not a connection; it is a `{type(connection).__name__}`."
            )

        if connection.engine.name == SQLiteDialect.DIALECT_NAME:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                include_schemas=True,
                include_object=include_schemas(schemas),
                render_as_batch=True,
            )
        elif connection.engine.name == PostgreSQLDialect.DIALECT_NAME:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                include_schemas=True,
                include_object=include_schemas(schemas),
            )
        else:
            raise Exception(
                f"Unsupported database dialect `{connection.engine.name}`. Expected one of {[SQLiteDialect.DIALECT_NAME, PostgreSQLDialect.DIALECT_NAME]}"
            )

    def _run_migrations(
        self, bases: list[MetaBase], connection: Connection | Connectable | Engine
    ):
        if connection.engine is None:
            raise Exception(
                "SQLAlchemy Session is not bound to an engine. This is not supported."
            )

        metadata = self.get_metadata(bases)
        schemas = metadata.schemas
        with context.begin_transaction():
            try:
                if connection.engine.name == "postgresql":
                    _ = connection.execute(
                        f"SET search_path TO {','.join(schemas + ['public'])};"
                    )
                context.run_migrations()
            except ProgrammingError as error:
                # This occurs when downgrading from the very last version
                # because the `alembic_version` table is dropped. The exception
                # can be safely ignored because the migration commits the transaction
                # before the failure, and there is nothing left for Alembic to do.
                if not (
                    type(error.orig) is UndefinedTable
                    and "DELETE FROM alembic_version" in error.statement
                ):
                    raise

    def run_migrations_offline(self, bases: list[MetaBase]):
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.

        """
        config = self.get_config()
        metadata = self.get_metadata(bases)
        target_metadata = metadata.target_metadata
        include_schemas = metadata.include_schemas
        schemas = metadata.schemas

        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            compare_type=True,
            include_schemas=True,
            include_object=include_schemas(schemas),
        )

        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online(self, bases: list[MetaBase]):
        """Run migrations in 'online' mode.

        In this scenario we need to create an Engine
        and associate a connection with the context.

        """
        config = self.get_config()

        connectable: Connectable | None = cast(dict[str, Any], config.attributes).get(
            "connection", None
        )

        if connectable:
            self._configure_context(bases, connectable)
            self._run_migrations(bases, connectable)
        else:
            connectable = engine_from_config(
                config.get_section(config.config_ini_section),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )

            with connectable.connect() as connection:
                self._configure_context(bases, connection)
                self._run_migrations(bases, connection)
