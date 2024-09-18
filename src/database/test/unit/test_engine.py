import re
from unittest.mock import patch

import pytest
from Ligare.database.engine import DatabaseEngine
from Ligare.database.engine.postgresql import PostgreSQLScopedSession
from Ligare.database.engine.sqlite import SQLiteScopedSession

# importing the fixtures makes pytest load them
from Ligare.database.testing import (
    mock_postgresql_connection,  # pyright: ignore[reportUnusedImport]
)
from Ligare.database.testing import MockPostgreSQLConnection
from mock import MagicMock
from pytest_mock import MockerFixture
from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import Pool, StaticPool
from sqlalchemy.pool.impl import NullPool, QueuePool

SQLITE_TEST_CONNECTION_STR = "sqlite:///:memory:"
POSTGRESQL_TEST_CONNECTION_STR = (
    "postgresql://example:example@255.255.255.255:1/example"
)


@pytest.mark.parametrize(
    "session_type,connection_string",
    [
        (SQLiteScopedSession, SQLITE_TEST_CONNECTION_STR),
        (PostgreSQLScopedSession, POSTGRESQL_TEST_CONNECTION_STR),
    ],
)
def test__DatabaseEngine__get_session_from_connection_string__returns_correct_session_type(
    connection_string: str,
    session_type: type[SQLiteScopedSession | PostgreSQLScopedSession],
    mocker: MockerFixture,
):
    _ = mocker.patch("Ligare.database.engine.sqlite.event")
    _ = mocker.patch("Ligare.database.engine.sqlite.create_engine")
    _ = mocker.patch("Ligare.database.engine.postgresql.create_engine")
    session = DatabaseEngine.get_session_from_connection_string(connection_string)
    assert isinstance(session, session_type)


def test__DatabaseEngine__get_session_from_connection_string__raises_exception_with_unknown_connection_string():
    # use a legitimate but unsupported (by Ligare.database) connection string
    connection_string = "mssql+pyodbc://localhost/noop"
    connection_string_serialized = f"{connection_string=}"
    with pytest.raises(
        ValueError,
        match=rf"^Unsupported connection string.+{re.escape(connection_string_serialized)}",
    ):
        _ = DatabaseEngine.get_session_from_connection_string(connection_string)


@pytest.mark.parametrize("connection_string", ["", "://", None, " ", "foo"])
def test__DatabaseEngine__get_session_from_connection_string__raises_exception_with_invalid_connection_string(
    connection_string: str,
):
    connection_string_serialized = f"{connection_string=}"
    with pytest.raises(
        ValueError,
        match=rf"^Invalid connection string.+{re.escape(connection_string_serialized)}",
    ):
        _ = DatabaseEngine.get_session_from_connection_string(connection_string)


@pytest.mark.parametrize(
    "session_type,module_name,connection_string",
    [
        (SQLiteScopedSession, "sqlite", SQLITE_TEST_CONNECTION_STR),
        (PostgreSQLScopedSession, "postgresql", POSTGRESQL_TEST_CONNECTION_STR),
    ],
)
def test__ScopedSession__create__creates_correct_engine_type(
    session_type: type[SQLiteScopedSession | PostgreSQLScopedSession],
    module_name: str,
    connection_string: str,
    mocker: MockerFixture,
):
    _ = mocker.patch("Ligare.database.engine.sqlite.event")
    create_engine_mock = mocker.patch(
        f"Ligare.database.engine.{module_name}.create_engine"
    )
    connection_string = "sqlite:///:memory:"
    session = session_type.create(connection_string)
    create_engine_mock.assert_called_once()
    assert create_engine_mock.call_args[0][0] == connection_string
    assert isinstance(session, session_type)


@pytest.mark.parametrize(
    "connection_string,connection_pool_type",
    [
        (SQLITE_TEST_CONNECTION_STR, StaticPool),
        ("sqlite:///dev/null", NullPool),
    ],
)
def test__SQLiteScopedSession__create__uses_correct_connection_pool_type(
    connection_string: str,
    connection_pool_type: type[Pool],
    mocker: MockerFixture,
):
    _ = mocker.patch("Ligare.database.engine.sqlite.event")
    session = SQLiteScopedSession.create(connection_string)
    assert isinstance(session.bind.pool, connection_pool_type)  # type: ignore[reportUnknownMemberType,reportAttributeAccessIssue,reportOptionalMemberAccess]


def test__SQLiteScopedSession__create__enables_foreign_key_constraints():
    session = SQLiteScopedSession.create(SQLITE_TEST_CONNECTION_STR, echo=True)
    statement = session().execute(
        "PRAGMA foreign_keys;"  # pyright: ignore[reportArgumentType]
    )
    assert statement.one() == (1,)


@patch.object(MetaData, "reflect", MagicMock())
@pytest.mark.parametrize(
    "connection_string,connection_pool_type",
    [
        (POSTGRESQL_TEST_CONNECTION_STR, QueuePool),
    ],
)
def test__PostgreSQLScopedSession__create__uses_correct_connection_pool_type(
    connection_string: str, connection_pool_type: type[QueuePool]
):
    session = PostgreSQLScopedSession.create(connection_string)
    assert isinstance(session.bind.pool, connection_pool_type)  # type: ignore[reportUnknownMemberType,reportAttributeAccessIssue,reportOptionalMemberAccess]


def test__PostgreSQLScopedSession__create__verifies_dependencies_installed(
    mocker: MockerFixture,
):
    _ = mocker.patch("Ligare.database.engine.postgresql.find_spec", return_value=None)

    with pytest.raises(ModuleNotFoundError):
        _ = PostgreSQLScopedSession.create(POSTGRESQL_TEST_CONNECTION_STR)


@patch.object(MetaData, "reflect", MagicMock())
@pytest.mark.parametrize(
    "session_type,connection_string",
    [
        (SQLiteScopedSession, SQLITE_TEST_CONNECTION_STR),
        (PostgreSQLScopedSession, POSTGRESQL_TEST_CONNECTION_STR),
    ],
)
def test__DatabaseEngine__create__does_not_require_schema_name(
    connection_string: str,
    session_type: type[SQLiteScopedSession | PostgreSQLScopedSession],
    mock_postgresql_connection: MockPostgreSQLConnection,
):
    class _Base:
        pass

    Base = declarative_base(cls=_Base)

    class Foo(Base):  # pyright: ignore[reportUntypedBaseClass]
        __tablename__ = "foo"
        foo_id = Column("foo_id", Integer, primary_key=True)

    _ = session_type.create(connection_string, echo=True, bases=[Base])

    assert Foo.__table__.schema is None  # pyright: ignore[reportUnknownMemberType]


@patch.object(MetaData, "reflect", MagicMock())
@pytest.mark.parametrize(
    "session_type,connection_string",
    [
        (SQLiteScopedSession, SQLITE_TEST_CONNECTION_STR),
        (PostgreSQLScopedSession, POSTGRESQL_TEST_CONNECTION_STR),
    ],
)
def test__ScopedSession__create__sets_table_schema_when_specified(
    connection_string: str,
    session_type: type[SQLiteScopedSession | PostgreSQLScopedSession],
    mock_postgresql_connection: MockPostgreSQLConnection,
):
    schema_name = "foo_schema"

    class _Base:
        __table_args__ = {"schema": schema_name}

    Base = declarative_base(cls=_Base)

    class Foo(Base):  # pyright: ignore[reportUntypedBaseClass]
        __tablename__ = "foo"
        foo_id = Column("foo_id", Integer, primary_key=True)

    _ = session_type.create(connection_string, echo=True, bases=[Base])

    assert Foo.__table__.schema == schema_name  # pyright: ignore[reportUnknownMemberType]


def test__SQLiteScopedSession__create__prepends_schema_to_table_name():
    schema_name = "foo_schema"
    tablename = "foo"

    class _Base:
        __table_args__ = {"schema": schema_name}

    Base = declarative_base(cls=_Base)

    class Foo(Base):  # pyright: ignore[reportUntypedBaseClass]
        __tablename__ = tablename
        foo_id = Column("foo_id", Integer, primary_key=True)

    _ = SQLiteScopedSession.create("sqlite:///:memory:", echo=True, bases=[Base])

    assert Foo.__tablename__ == f"{schema_name}.{tablename}"
    assert Foo.__table__.name == f"{schema_name}.{tablename}"  # pyright: ignore[reportUnknownMemberType]
    assert Foo.__table__.fullname == f"{schema_name}.{schema_name}.{Foo.__tablename__}"  # pyright: ignore[reportUnknownMemberType]


@patch.object(MetaData, "reflect", MagicMock())
@pytest.mark.parametrize(
    "first_session_type,second_session_type",
    [
        (SQLiteScopedSession, PostgreSQLScopedSession),
        (PostgreSQLScopedSession, SQLiteScopedSession),
        (SQLiteScopedSession, SQLiteScopedSession),
        (PostgreSQLScopedSession, PostgreSQLScopedSession),
    ],
)
def test__ScopedSession__create__correctly_resets_schema_when_creating_engine_multiple_times(
    first_session_type: type[SQLiteScopedSession] | type[PostgreSQLScopedSession],
    second_session_type: type[SQLiteScopedSession] | type[PostgreSQLScopedSession],
    mock_postgresql_connection: MockPostgreSQLConnection,
):
    schema_name = "foo_schema"
    tablename = "foo"

    class _Base:
        __table_args__ = {"schema": schema_name}

    Base = declarative_base(cls=_Base)

    class Foo(Base):  # pyright: ignore[reportUntypedBaseClass]
        __tablename__ = tablename
        foo_id = Column("foo_id", Integer, primary_key=True)

    _ = first_session_type.create(SQLITE_TEST_CONNECTION_STR, echo=True, bases=[Base])
    _ = second_session_type.create(
        POSTGRESQL_TEST_CONNECTION_STR, echo=True, bases=[Base]
    )

    if second_session_type is SQLiteScopedSession:
        assert Foo.__tablename__ == f"{schema_name}.{tablename}"
        assert Foo.__table__.name == f"{schema_name}.{tablename}"  # pyright: ignore[reportUnknownMemberType]
        assert (
            Foo.__table__.fullname == f"{schema_name}.{schema_name}.{Foo.__tablename__}"  # pyright: ignore[reportUnknownMemberType]
        )
    else:
        assert Foo.__tablename__ == tablename
        assert Foo.__table__.name == tablename  # pyright: ignore[reportUnknownMemberType]
        assert Foo.__table__.fullname == f"{schema_name}.{tablename}"  # pyright: ignore[reportUnknownMemberType]
