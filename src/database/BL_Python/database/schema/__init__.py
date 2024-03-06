from BL_Python.database.types import Op
from sqlalchemy.engine import Dialect

from .postgresql import PostgreSQLDialect
from .sqlite import SQLiteDialect

_dialect_type_map = {"sqlite": SQLiteDialect, "postgresql": PostgreSQLDialect}


def get_type_from_dialect(dialect: Dialect):
    return _dialect_type_map[dialect.name](dialect)


def get_type_from_op(op: Op):
    dialect: Dialect = op.get_bind().dialect
    return get_type_from_dialect(dialect)
