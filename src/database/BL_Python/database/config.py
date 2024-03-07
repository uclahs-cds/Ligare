from BL_Python.programming.config import AbstractConfig
from pydantic import BaseModel


class DatabaseConnectArgsConfig(BaseModel):
    sslmode: str = ""
    options: str = ""


class DatabaseConfig(BaseModel, AbstractConfig):
    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False
    connect_args: DatabaseConnectArgsConfig | None = None


class Config(BaseModel, AbstractConfig):
    database: DatabaseConfig
