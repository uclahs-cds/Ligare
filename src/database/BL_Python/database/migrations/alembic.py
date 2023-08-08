import logging
from configparser import ConfigParser
from dataclasses import dataclass
from functools import lru_cache
from logging.config import fileConfig
from typing import Any, List, Optional, Protocol, cast

from alembic import context
from psycopg2.errors import UndefinedTable
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connectable, Connection, Engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.sql.schema import MetaData, Table

from BL_Python.database.migrations import DialectHelper, MetaBaseType


class type_include_object(Protocol):
    def __call__(
        self,
        object: Table,
        name: str,
        type_: str,
        reflected: Any,
        compare_to: Any,
    ) -> bool:
        ...


class type_include_schemas(Protocol):
    def __call__(self, names: list[str]) -> type_include_object:
        ...


@dataclass
class type_metadata:
    include_schemas: type_include_schemas
    target_metadata: List[MetaData]
    schemas: List[str]


class AlembicEnvSetup:
    _connection_string: str
    _bases: list[MetaBaseType]

    def __init__(self, connection_string: str, bases: list[MetaBaseType]) -> None:
        self._connection_string = connection_string
        self._bases = bases

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

        config.set_main_option("sqlalchemy.url", self._connection_string)

        return config

    @lru_cache(maxsize=1)
    def get_metadata(self):
        # add your model's MetaData object here
        # for 'autogenerate' support
        # from myapp import mymodel
        # target_metadata = mymodel.Base.metadata
        # from CAP.database.models.CAP import Base
        # from CAP.database.models.identity import IdentityBase
        # from CAP.database.models.platform import PlatformBase

        def include_schemas(names: List[str]):
            def include_object(
                object: Table,
                name: str,
                type_: str,
                reflected: Any,
                compare_to: Any,
            ):
                if type_ == "table":
                    return object.schema in names
                return True

            return include_object

        target_metadata = [base.metadata for base in self._bases]
        schemas: list[str] = []
        for base in self._bases:
            schema = DialectHelper.get_schema(base)
            if schema is not None:
                schemas.append(schema)

        return type_metadata(include_schemas, target_metadata, schemas)

    def _configure_context(self, connection: Connection | Connectable | Engine):
        metadata = self.get_metadata()
        target_metadata = metadata.target_metadata
        include_schemas = metadata.include_schemas
        schemas = metadata.schemas

        if connection.engine is not None and connection.engine.name == "sqlite":
            context.configure(
                connection=cast(Connection, connection),
                target_metadata=target_metadata,
                compare_type=True,
                include_schemas=True,
                include_object=include_schemas(schemas),
                render_as_batch=True,
            )
        else:
            context.configure(
                connection=cast(Connection, connection),
                target_metadata=target_metadata,
                compare_type=True,
                include_schemas=True,
                include_object=include_schemas(schemas),
            )

    def _run_migrations(self, connection: Connection | Connectable | Engine):
        if connection.engine is None:
            raise Exception(
                "SQLAlchemy Session is not bound to an engine. This is not supported."
            )

        metadata = self.get_metadata()
        schemas = metadata.schemas
        with context.begin_transaction():
            try:
                if connection.engine.name == "postgresql":
                    _ = connection.execute(
                        f"SET search_path TO {','.join(schemas)},public;"
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

    def run_migrations_offline(self, connection_string: str):
        """Run migrations in 'offline' mode.

        This configures the context with just a URL
        and not an Engine, though an Engine is acceptable
        here as well.  By skipping the Engine creation
        we don't even need a DBAPI to be available.

        Calls to context.execute() here emit the given string to the
        script output.

        """

        config = self.get_config()
        metadata = self.get_metadata()
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

    def run_migrations_online(self, connection_string: str):
        """Run migrations in 'online' mode.

        In this scenario we need to create an Engine
        and associate a connection with the context.

        """
        config = self.get_config()

        connectable: Connectable = cast(dict[Any, Any], config.attributes).get(
            "connection", None
        )

        if connectable:
            self._configure_context(connectable)
            self._run_migrations(connectable)
        else:
            connectable = engine_from_config(
                config.get_section(config.config_ini_section),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )

            with connectable.connect() as connection:
                self._configure_context(connection)
                self._run_migrations(connection)
