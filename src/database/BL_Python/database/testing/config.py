from typing import Any, Callable, Generator, Protocol

from BL_Python.database.config import DatabaseConfig
from BL_Python.programming.collections.dict import AnyDict, merge
from BL_Python.programming.config import TConfig, load_config

TConfigCallable = Callable[[type[TConfig], str, AnyDict | None], TConfig]
UseInmemoryDatabaseResult = Generator[
    tuple[TConfigCallable[TConfig], TConfigCallable[TConfig]], Any, None
]


class UseInmemoryDatabase(Protocol):
    def __call__(
        self,
        config_type: type[TConfig],
        toml_file_path: str,
        config_overrides: AnyDict | None = None,
    ) -> TConfig: ...


def inmemory_database_config():
    return DatabaseConfig(
        connection_string="sqlite:///:memory:?check_same_thread=False"
    )


def inmemory_database_config_loader() -> UseInmemoryDatabase:
    def inmemory_database_config_loader(
        config_type: type[TConfig],
        toml_file_path: str,
        config_overrides: AnyDict | None = None,
    ) -> TConfig:
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

    return inmemory_database_config_loader
