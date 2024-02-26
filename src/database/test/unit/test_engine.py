import re

import pytest
from BL_Python.database.engine import DatabaseEngine
from BL_Python.database.engine.postgresql import PostgreSQLScopedSession
from BL_Python.database.engine.sqlite import SQLiteScopedSession
from pytest_mock import MockerFixture
from sqlalchemy.pool import Pool, StaticPool
from sqlalchemy.pool.impl import NullPool


@pytest.mark.parametrize(
    "connection_string,session_type",
    [
        ("sqlite:///:memory:", SQLiteScopedSession),
        ("postgresql://localhost/noop", PostgreSQLScopedSession),
    ],
)
def test__DatabaseEngine__get_session_from_connection_string__returns_correct_session_type(
    connection_string: str,
    session_type: type[SQLiteScopedSession | PostgreSQLScopedSession],
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.database.engine.sqlite.event")
    _ = mocker.patch("BL_Python.database.engine.sqlite.create_engine")
    _ = mocker.patch("BL_Python.database.engine.postgresql.create_engine")
    session = DatabaseEngine.get_session_from_connection_string(connection_string)
    assert isinstance(session, session_type)


def test__DatabaseEngine__get_session_from_connection_string__raises_exception_with_unknown_connection_string():
    # use a legitimate but unsupported (by BL_Python.database) connection string
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
    "connection_string,session_type,module_name",
    [
        ("sqlite:///:memory:", SQLiteScopedSession, "sqlite"),
        ("postgresql://localhost/noop", PostgreSQLScopedSession, "postgresql"),
    ],
)
def test__ScopedSession__create__creates_correct_engine_type(
    connection_string: str,
    session_type: type[SQLiteScopedSession | PostgreSQLScopedSession],
    module_name: str,
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.database.engine.sqlite.event")
    create_engine_mock = mocker.patch(
        f"BL_Python.database.engine.{module_name}.create_engine"
    )
    connection_string = "sqlite:///:memory:"
    session = session_type.create(connection_string)
    create_engine_mock.assert_called_once()
    assert create_engine_mock.call_args[0][0] == connection_string
    assert isinstance(session, session_type)


@pytest.mark.parametrize(
    "connection_string,connection_pool_type",
    [
        ("sqlite:///:memory:", StaticPool),
        ("sqlite:///dev/null", NullPool),
    ],
)
def test__SQLiteScopedSession__create__uses_correct_connection_pool_type(
    connection_string: str,
    connection_pool_type: type[Pool],
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.database.engine.sqlite.event")
    session = SQLiteScopedSession.create(connection_string)
    assert isinstance(session.bind.pool, connection_pool_type)  # type: ignore[reportUnknownMemberType,reportAttributeAccessIssue,reportOptionalMemberAccess]


def test__SQLiteScopedSession__create__enables_foreign_key_constraints():
    connection_string = "sqlite:///:memory:"
    session = SQLiteScopedSession.create(connection_string, echo=True)
    statement = session().execute(
        "PRAGMA foreign_keys;"  # pyright: ignore[reportArgumentType]
    )
    assert statement.one() == (1,)
