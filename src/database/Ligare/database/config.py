from typing import Any

from Ligare.programming.config import AbstractConfig
from pydantic import BaseModel
from pydantic.config import ConfigDict
from typing_extensions import override


class DatabaseConnectArgsConfig(BaseModel):
    # allow any values, as this type is not
    # specifically the type to be used elsewhere
    model_config = ConfigDict(extra="allow")


class PostgreSQLDatabaseConnectArgsConfig(DatabaseConnectArgsConfig):
    # ignore anything that DatabaseConnectArgsConfig
    # allowed to be set, except for any other attributes
    # of this class, which will end up assigned through
    # the instatiation of the __init__ override of DatabaseConfig
    model_config = ConfigDict(extra="ignore")

    sslmode: str = ""
    options: str = ""


class SQLiteDatabaseConnectArgsConfig(DatabaseConnectArgsConfig):
    model_config = ConfigDict(extra="ignore")


class DatabaseConfig(BaseModel, AbstractConfig):
    def __init__(self, **data: Any):
        super().__init__(**data)

        model_data = self.connect_args.model_dump() if self.connect_args else {}
        if self.connection_string.startswith("sqlite://"):
            self.connect_args = SQLiteDatabaseConnectArgsConfig(**model_data)
        elif self.connection_string.startswith("postgresql://"):
            self.connect_args = PostgreSQLDatabaseConnectArgsConfig(**model_data)

    @override
    def post_load(self) -> None:
        return super().post_load()

    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False
    # the static field allows Pydantic to store
    # values from a dictionary
    connect_args: DatabaseConnectArgsConfig | None = None


class Config(BaseModel, AbstractConfig):
    @override
    def post_load(self) -> None:
        return super().post_load()

    database: DatabaseConfig
