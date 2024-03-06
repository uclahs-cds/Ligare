from typing import final

from BL_Python.database.schema.dialect import DialectBase
from sqlalchemy.engine import Dialect
from typing_extensions import override


@final
class SQLiteDialect(DialectBase):
    _dialect: Dialect
    supports_schemas: bool = False

    def __init__(self, dialect: Dialect) -> None:
        self._dialect = dialect

    @property
    @override
    def dialect(self) -> Dialect:
        return self._dialect

    @property
    @override
    def get_timestamp_sql(self):
        return "CURRENT_TIMESTAMP"
