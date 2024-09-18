from typing import Any, Callable, Generator

import pytest
from Ligare.database.testing.config import (
    UseInmemoryDatabaseLoader,
    inmemory_database_config_loader,
)
from Ligare.programming.collections.dict import AnyDict
from Ligare.programming.config import TConfig
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
        mocker.patch("Ligare.web.application.load_config", loader),
        mocker.patch("Ligare.database.migrations.alembic.env.load_config", loader),
    )
