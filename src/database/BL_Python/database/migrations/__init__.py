from typing import TYPE_CHECKING, List, Optional, Protocol, cast, final

from sqlalchemy.orm import DeclarativeMeta

MetaBaseType = Type[DeclarativeMeta]

if TYPE_CHECKING:
    from typing import Dict, Protocol, Type, TypeVar, Union

    from sqlalchemy.engine import Dialect

    TBase = TypeVar("TBase")

    class TableNameCallback(Protocol):
        def __call__(
            self,
            dialect_schema: "Union[str, None]",
            full_table_name: str,
            base_table: str,
            meta_base: MetaBaseType,
        ) -> None: ...

    class Connection(Protocol):
        dialect: Dialect

    class Op(Protocol):
        @staticmethod
        def get_bind() -> Connection: ...


@final
class DialectHelper:
    """
    Utilities to get database schema and table names
    for different SQL dialects and database engines.

    For example, PostgreSQL supports schemas. This means:
        * get_dialect_schema(meta) returns a schema name, if there is one, e.g. "cap"
        * get_full_table_name(table_name, meta) returns the schema name, followed by the table name, e.g. " cap.assay_plate "

    SQLite does not support schemas. This means:
        * get_dialect_schema(meta) returns None
        * get_full_table_name(table_name, meta) returns the table name, with the schema name prepended to it, e.g. " 'cap.assay_plate' "
                                                The key difference is that there is no schema, and the table name comes from the SQLite
                                                engine instantiation, which prepends the "schema" to the table name.
    """

    dialect: "Dialect"
    dialect_supports_schemas: bool

    def __init__(self, dialect: "Dialect"):
        self.dialect = dialect
        # right now we only care about SQLite and PSQL,
        # so if the dialect is PSQL, then we consider the
        # dialect to support schemas, otherwise it does not.
        self.dialect_supports_schemas = dialect.name == "postgresql"

    @staticmethod
    def get_schema(meta: "MetaBaseType"):
        table_args = cast(
            Optional[dict[str, str]], getattr(meta, "__table_args__", None)
        )
        if table_args is None:
            return None
        return table_args.get("schema")

    def get_dialect_schema(self, meta: "MetaBaseType"):
        """Get the database schema as a string, or None if the dialect does not support schemas."""
        if not self.dialect_supports_schemas:
            return None
        return DialectHelper.get_schema(meta)

    def get_full_table_name(self, table_name: str, meta: "MetaBaseType"):
        """
        If the dialect supports schemas, then the table name does not have the schema prepended.
        In dialects that don't support schemas, e.g., SQLite, the table name has the schema prepended.
        This is because, when schemas are supported, the dialect automatically handles which schema
        to use, while non-schema dialects do not reference any schemas.
        """
        if self.get_dialect_schema(meta):
            return table_name
        else:
            return f"{DialectHelper.get_schema(meta)}.{table_name}"

    def get_timestamp_sql(self):
        timestamp_default_sql = "now()"
        if self.dialect.name == "sqlite":
            timestamp_default_sql = "CURRENT_TIMESTAMP"
        return timestamp_default_sql

    @staticmethod
    def iterate_table_names(
        op: "Op",
        schema_tables: "Dict[MetaBaseType, List[str]]",
        table_name_callback: "TableNameCallback",
    ):
        """
        Call `table_name_callback` once for every table in every Base.

        op: The `op` object from Alembic.
        schema_tables: A dictionary of the tables this call applies to for every Base.
        table_name_callback: A callback executed for every table in `schema_tables`.
        """
        dialect: Dialect = op.get_bind().dialect
        schema = DialectHelper(dialect)
        get_full_table_name = schema.get_full_table_name
        get_dialect_schema = schema.get_dialect_schema

        for meta_base, schema_base_tables in schema_tables.items():
            dialect_schema = get_dialect_schema(meta_base)
            for base_table in schema_base_tables:
                full_table_name = get_full_table_name(base_table, meta_base)
                table_name_callback(
                    dialect_schema, full_table_name, base_table, meta_base
                )
