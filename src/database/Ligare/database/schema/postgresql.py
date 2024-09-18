from typing import final

from Ligare.database.schema.dialect import DialectBase
from sqlalchemy.engine import Dialect
from typing_extensions import override


@final
class PostgreSQLDialect(DialectBase):
    DIALECT_NAME = "postgresql"
    _dialect: Dialect
    supports_schemas: bool = True

    def __init__(self, dialect: Dialect) -> None:
        if dialect.name != PostgreSQLDialect.DIALECT_NAME:
            raise ValueError(
                f"Invalid Dialect with name `{dialect.name}` provided for `{PostgreSQLDialect.__name__}`. Expected `{self.DIALECT_NAME}`."
            )
        self._dialect = dialect

    @property
    @override
    def dialect(self) -> Dialect:
        return self._dialect

    @property
    @override
    def timestamp_sql(self):
        return "now()"
