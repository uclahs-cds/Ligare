from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False
