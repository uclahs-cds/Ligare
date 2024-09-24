from typing import Any as Any
from typing import Generator, cast
from unittest.mock import AsyncMock, MagicMock, NonCallableMagicMock

import pytest
from injector import Injector
from Ligare.database.config import Config
from Ligare.database.dependency_injection import get_database_ioc_container
from Ligare.database.migrations.alembic.env import set_up_database as _set_up_database
from Ligare.database.testing.config import inmemory_database_config
from Ligare.database.types import MetaBase
from mock import MagicMock
from pytest import FixtureRequest
from pytest_mock import MockerFixture
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import Session
from sqlalchemy.pool.impl import QueuePool

MockPostgreSQLConnection = Generator[
    MagicMock | AsyncMock | NonCallableMagicMock, MagicMock, None
]

SetUpDatabaseFixture = tuple[Session, Connection]


@pytest.fixture
def mock_postgresql_connection(mocker: MockerFixture) -> MockPostgreSQLConnection:
    yield mocker.patch(
        "sqlalchemy.pool.QueuePool", spec=QueuePool, __bases__=MagicMock()
    )


def _set_up_database_container(bases: list[MetaBase | type[MetaBase]]):
    database_config = inmemory_database_config()
    config = Config(database=database_config)

    return get_database_ioc_container(config, bases=bases)


def _get_bases_parameter(request: FixtureRequest) -> list[MetaBase | type[MetaBase]]:
    if not hasattr(request, "param"):
        raise Exception(
            f"`{set_up_database.__name__}` requires an the indirect parameter of type `list[type[MetaBase]]`."
        )

    return cast(list[MetaBase | type[MetaBase]], request.param)


@pytest.fixture
def set_up_database_container(request: FixtureRequest) -> Injector:
    bases = _get_bases_parameter(request)

    return _set_up_database_container(bases)


@pytest.fixture
def set_up_database(
    request: FixtureRequest,
) -> Generator[tuple[Session, Connection], Any, None]:
    bases = _get_bases_parameter(request)

    container = _set_up_database_container(bases)

    with container.get(Session) as session:
        if session.bind is None:
            raise Exception(
                "SQLAlchemy Session is not bound to an engine. This is not supported."
            )
        with _set_up_database(session.bind.engine) as connection:
            yield (session, connection)
