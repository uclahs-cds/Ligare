from typing import final

from Ligare.database.schema.dialect import DialectBase
from sqlalchemy.engine import Dialect
from typing_extensions import override


@final
class SQLiteDialect(DialectBase):
    DIALECT_NAME = "sqlite"
    _dialect: Dialect
    supports_schemas: bool = False

    def __init__(self, dialect: Dialect) -> None:
        if dialect.name != SQLiteDialect.DIALECT_NAME:
            raise ValueError(
                f"Invalid Dialect with name `{dialect.name}` provided for `{SQLiteDialect.__name__}`. Expected `{self.DIALECT_NAME}`."
            )

        self._dialect = dialect

    @property
    @override
    def dialect(self) -> Dialect:
        return self._dialect

    @property
    @override
    def timestamp_sql(self):
        return "CURRENT_TIMESTAMP"
