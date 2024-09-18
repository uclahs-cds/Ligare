import pytest
from alembic.operations.base import Operations
from Ligare.database.schema import get_type_from_dialect, get_type_from_op
from Ligare.database.schema.postgresql import PostgreSQLDialect
from Ligare.database.schema.sqlite import SQLiteDialect
from mock import MagicMock
from sqlalchemy.engine import Dialect


@pytest.mark.parametrize(
    "dialect_name,expected_type",
    [("sqlite", SQLiteDialect), ("postgresql", PostgreSQLDialect)],
)
def test__get_type_from_dialect__returns_correct_dialect_instance(
    dialect_name: str, expected_type: type[SQLiteDialect] | type[PostgreSQLDialect]
):
    dialect = Dialect()
    dialect.name = dialect_name
    dialect_type = get_type_from_dialect(dialect)
    assert isinstance(dialect_type, expected_type)


def test__get_type_from_dialect__raises_exception_when_given_unknown_dialect():
    dialect_name = "mssql"
    dialect = Dialect()
    dialect.name = dialect_name

    with pytest.raises(
        ValueError, match=rf"Unexpected dialect with name `{dialect_name}`.+"
    ):
        _ = get_type_from_dialect(dialect)


@pytest.mark.parametrize(
    "dialect_name,expected_type",
    [("sqlite", SQLiteDialect), ("postgresql", PostgreSQLDialect)],
)
def test__get_type_from_op__returns_correct_dialect_instance(
    dialect_name: str, expected_type: type[SQLiteDialect] | type[PostgreSQLDialect]
):
    dialect = Dialect()
    dialect.name = dialect_name
    migration_context = MagicMock(impl=MagicMock(bind=MagicMock(dialect=dialect)))
    op = Operations(migration_context)
    dialect_type = get_type_from_op(op)
    assert isinstance(dialect_type, expected_type)


def test__get_type_from_op__raises_exception_when_given_unknown_dialect():
    dialect_name = "mssql"
    dialect = Dialect()
    dialect.name = dialect_name
    migration_context = MagicMock(impl=MagicMock(bind=MagicMock(dialect=dialect)))
    op = Operations(migration_context)

    with pytest.raises(
        ValueError, match=rf"Unexpected dialect with name `{dialect_name}`.+"
    ):
        _ = get_type_from_op(op)
