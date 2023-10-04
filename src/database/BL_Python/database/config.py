from BL_Python.programming.config import AbstractConfig
from pydantic import BaseModel


class DatabaseConfig(BaseModel, AbstractConfig):
    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False
