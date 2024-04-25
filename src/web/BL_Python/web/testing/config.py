from typing import Any, Callable, Generator

import pytest
from BL_Python.database.testing.config import (
    UseInmemoryDatabaseLoader,
    inmemory_database_config_loader,
)
from BL_Python.programming.collections.dict import AnyDict
from BL_Python.programming.config import TConfig
from pytest_mock import MockerFixture

TConfigCallable = Callable[[type[TConfig], str, AnyDict | None], TConfig]
UseInmemoryDatabaseResult = Generator[
    tuple[UseInmemoryDatabaseLoader, UseInmemoryDatabaseLoader], Any, None
]


@pytest.fixture
def use_inmemory_database(
    mocker: MockerFixture,
) -> UseInmemoryDatabaseResult:
    loader = inmemory_database_config_loader()
    yield (
        mocker.patch("BL_Python.web.application.load_config", loader),
        mocker.patch("BL_Python.database.migrations.alembic.env.load_config", loader),
    )
