from abc import ABC, abstractmethod

from Ligare.database.types import MetaBase, TableNameCallback
from sqlalchemy.engine import Dialect


class DialectBase(ABC):
    supports_schemas: bool = False

    @staticmethod
    def get_schema(meta: MetaBase) -> str | None:
        table_args = hasattr(meta, "__table_args__") and meta.__table_args__ or None

        if isinstance(table_args, dict):
            return table_args.get("schema")

        return None

    @staticmethod
    def iterate_table_names(
        dialect: "DialectBase",
        schema_tables: dict[MetaBase, list[str]],
        table_name_callback: TableNameCallback,
    ) -> None:
        """
        Call `table_name_callback` once for every table in every Base.

        op: The `op` object from Alembic.
        schema_tables: A dictionary of the tables this call applies to for every Base.
        table_name_callback: A callback executed for every table in `schema_tables`.
        """
        get_full_table_name = dialect.get_full_table_name
        get_dialect_schema = dialect.get_dialect_schema

        for meta_base, schema_base_tables in schema_tables.items():
            dialect_schema = get_dialect_schema(meta_base)
            for base_table in schema_base_tables:
                full_table_name = get_full_table_name(base_table, meta_base)
                table_name_callback(
                    dialect_schema, full_table_name, base_table, meta_base
                )

    def get_dialect_schema(self, meta: MetaBase) -> str | None:
        if self.supports_schemas:
            return DialectBase.get_schema(meta)

        return None

    def get_full_table_name(self, table_name: str, meta: MetaBase) -> str:
        """
        If the dialect supports schemas, then the table name does not have the schema prepended.
        In dialects that don't support schemas, e.g., SQLite, the table name has the schema prepended.
        This is because, when schemas are supported, the dialect automatically handles which schema
        to use, while non-schema dialects do not reference any schemas.
        """
        if self.get_dialect_schema(meta):
            return table_name
        else:
            return f"{DialectBase.get_schema(meta)}.{table_name}"

    @property
    @abstractmethod
    def dialect(self) -> Dialect: ...  # pragma: nocover

    @property
    @abstractmethod
    def timestamp_sql(self) -> str: ...  # pragma: nocover
