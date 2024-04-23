from typing import Any, Callable, Generator

import pytest
from BL_Python.programming.collections.dict import AnyDict, merge
from BL_Python.programming.config import TConfig, load_config
from pytest_mock import MockerFixture

TConfigCallable = Callable[[type[TConfig], str, AnyDict | None], TConfig]
UseInmemoryDatabaseResult = Generator[
    tuple[TConfigCallable[TConfig], TConfigCallable[TConfig]], Any, None
]
UseInmemoryDatabase = Callable[[MockerFixture], UseInmemoryDatabaseResult[TConfig]]


@pytest.fixture
def use_inmemory_database(
    mocker: MockerFixture,
) -> UseInmemoryDatabaseResult[TConfig]:
    def load_config_override(
        config_type: type[TConfig],
        toml_file_path: str,
        config_overrides: AnyDict | None = None,
    ):
        """Used to force an SQLite in-memory database for tests."""
        return load_config(
            config_type=config_type,
            toml_file_path=toml_file_path,
            config_overrides=merge(
                {
                    "database": {
                        "connection_string": "sqlite:///:memory:?check_same_thread=False"
                    }
                },
                config_overrides or {},
                skip_existing=True,
            ),
        )

    # FIXME temporary?
    yield (
        mocker.patch("BL_Python.web.application.load_config", load_config_override),
        mocker.patch(
            "BL_Python.database.migrations.alembic.env.load_config",
            load_config_override,
        ),
    )
