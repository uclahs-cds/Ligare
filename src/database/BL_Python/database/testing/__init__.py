from typing import Any as Any
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, NonCallableMagicMock

import pytest
from mock import MagicMock
from pytest_mock import MockerFixture
from sqlalchemy.pool.impl import QueuePool

MockPostgreSQLConnection = Generator[
    MagicMock | AsyncMock | NonCallableMagicMock, MagicMock, None
]


@pytest.fixture
def mock_postgresql_connection(mocker: MockerFixture) -> MockPostgreSQLConnection:
    yield mocker.patch(
        "sqlalchemy.pool.QueuePool", spec=QueuePool, __bases__=MagicMock()
    )
