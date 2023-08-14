from typing import Any, Optional

import toml
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class LoggingConfig:
    log_level: str = "INFO"


@dataclass(frozen=True)
class FlaskOpenApiConfig:
    spec_path: Optional[str] = None
    validate_responses: bool = False


@dataclass(frozen=True)
class FlaskSessionCookieConfig:
    secret_key: str = "abc123"
    httponly: bool = True
    secure: bool = True
    samesite: str = "None"


@dataclass(frozen=True)
class FlaskSessionConfig:
    cookie: FlaskSessionCookieConfig
    permanent: bool = True
    lifetime: int = 86400
    refresh_each_request: bool = True


@dataclass(frozen=True)
class FlaskConfig:
    app_name: str = "app"
    env: str = "Development"
    openapi: Optional[FlaskOpenApiConfig] = None
    session: Optional[FlaskSessionConfig] = None


@dataclass(frozen=True)
class DatabaseConfig:
    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False


@dataclass(frozen=True)
class SAML2Config:
    metadata: Optional[str] = None
    metadata_url: Optional[str] = None
    relay_state: Optional[str] = None
    # TODO is there a more specific type than `Any`
    # that fits logging configurations?
    logging: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class Config:
    logging: LoggingConfig = LoggingConfig()
    flask: Optional[FlaskConfig] = None
    database: Optional[DatabaseConfig] = None
    saml2: Optional[SAML2Config] = None


def load_config(toml_file_path: str):
    config_dict = toml.load(toml_file_path)
    return Config(**config_dict)
