from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False
