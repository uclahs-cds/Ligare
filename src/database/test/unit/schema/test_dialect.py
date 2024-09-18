from typing import ClassVar

import pytest
from Ligare.database.schema.dialect import DialectBase
from Ligare.database.schema.postgresql import PostgreSQLDialect
from Ligare.database.schema.sqlite import SQLiteDialect
from Ligare.database.types import MetaBase
from Ligare.programming.str import get_random_str
from mock import MagicMock
from sqlalchemy import Column, Integer
from sqlalchemy.engine import Dialect
from sqlalchemy.ext.declarative import declarative_base


def get_test_table(schema_name: str | None = "foo_schema"):
    if schema_name is None:

        class _Base: ...  # pyright: ignore[reportRedeclaration]

    else:

        class _Base:
            __table_args__ = {"schema": schema_name}

    Base = declarative_base(cls=_Base)

    class Foo(Base):  # pyright: ignore[reportUntypedBaseClass]
        __tablename__: ClassVar = "foo"
        foo_id = Column("foo_id", Integer, primary_key=True)

    class Bar(Base):  # pyright: ignore[reportUntypedBaseClass]
        __tablename__: ClassVar = "bar"
        bar_id = Column("bar_id", Integer, primary_key=True)

    return (schema_name, [Foo, Bar], _Base)


@pytest.fixture
def test_table(schema_name: str | None = "foo_schema"):
    return get_test_table(schema_name)


@pytest.mark.parametrize("schema_name", ["foo_schema", None])
def test__DialectBase__get_schema__returns_correct_table_schema_name(
    schema_name: str | None,
):
    (table_schema_name, tables, _) = get_test_table(schema_name)

    schema = DialectBase.get_schema(tables[0])

    assert schema == table_schema_name


@pytest.mark.parametrize("dialect_type", [SQLiteDialect, PostgreSQLDialect])
def test__DialectBase__init__raises_error_when_wrong_dialect_used(
    dialect_type: type[SQLiteDialect] | type[PostgreSQLDialect],
):
    dialect = Dialect()
    dialect.name = get_random_str()
    with pytest.raises(
        ValueError, match=rf"Invalid Dialect with name `{dialect.name}`.+"
    ):
        _ = dialect_type(dialect)


@pytest.mark.parametrize(
    "dialect_type,expected_schema_name",
    [(SQLiteDialect, None), (PostgreSQLDialect, "foo_schema")],
)
def test__DialectBase__get_dialect_schema__returns_expected_schema_name(
    dialect_type: type[SQLiteDialect] | type[PostgreSQLDialect],
    expected_schema_name: str,
    test_table: tuple[str, list[MetaBase], MetaBase],
):
    (_, tables, _) = test_table
    dialect = Dialect()
    dialect.name = dialect_type.DIALECT_NAME
    test_dialect = dialect_type(dialect)

    schema = test_dialect.get_dialect_schema(tables[0])

    assert schema == expected_schema_name


@pytest.mark.parametrize(
    "dialect_type,expected_table_name",
    [(SQLiteDialect, "foo_schema.foo"), (PostgreSQLDialect, "foo")],
)
def test__DialectBase__get_full_table_name__returns_expected_table_name(
    dialect_type: type[SQLiteDialect] | type[PostgreSQLDialect],
    expected_table_name: str,
    test_table: tuple[str, list[MetaBase], MetaBase],
):
    (_, tables, _) = test_table
    dialect = Dialect()
    dialect.name = dialect_type.DIALECT_NAME
    test_dialect = dialect_type(dialect)

    table_name = test_dialect.get_full_table_name("foo", tables[0])

    assert table_name == expected_table_name


@pytest.mark.parametrize(
    "dialect_type",
    [SQLiteDialect, PostgreSQLDialect],
)
def test__DialectBase__iterate_table_names__calls_callback_for_every_table_in_metabase(
    dialect_type: type[SQLiteDialect] | type[PostgreSQLDialect],
    test_table: tuple[str, list[MetaBase], MetaBase],
):
    (schema_name, tables, meta_base) = test_table
    dialect = Dialect()
    dialect.name = dialect_type.DIALECT_NAME
    test_dialect = dialect_type(dialect)
    schema_tables = {meta_base: [table.__tablename__ for table in tables]}
    table_name_callback = MagicMock()

    test_dialect.iterate_table_names(test_dialect, schema_tables, table_name_callback)

    if test_dialect.supports_schemas:
        table_name_callback.assert_any_call(
            schema_name, tables[0].__tablename__, tables[0].__tablename__, meta_base
        )
        table_name_callback.assert_any_call(
            schema_name, tables[1].__tablename__, tables[1].__tablename__, meta_base
        )
    else:
        table_name_callback.assert_any_call(
            None,
            f"{schema_name}.{tables[0].__tablename__}",
            tables[0].__tablename__,
            meta_base,
        )
        table_name_callback.assert_any_call(
            None,
            f"{schema_name}.{tables[1].__tablename__}",
            tables[1].__tablename__,
            meta_base,
        )


@pytest.mark.parametrize(
    "dialect_name,dialect_type",
    [("sqlite", SQLiteDialect), ("postgresql", PostgreSQLDialect)],
)
def test__get_type_from_dialect__dialect_type_uses_correct_sqlalchemy_dialect(
    dialect_name: str, dialect_type: type[SQLiteDialect] | type[PostgreSQLDialect]
):
    dialect = Dialect()
    dialect.name = dialect_type.DIALECT_NAME
    test_dialect = dialect_type(dialect)
    assert test_dialect.dialect.name == dialect_name


@pytest.mark.parametrize(
    "dialect_type,expected_sql",
    [
        (SQLiteDialect, "CURRENT_TIMESTAMP"),
        (PostgreSQLDialect, "now()"),
    ],
)
def test__get_type_from_dialect__dialect_type_uses_correct_timestamp_sql(
    dialect_type: type[SQLiteDialect] | type[PostgreSQLDialect],
    expected_sql: str,
):
    dialect = Dialect()
    dialect.name = dialect_type.DIALECT_NAME
    test_dialect = dialect_type(dialect)
    assert test_dialect.timestamp_sql == expected_sql
