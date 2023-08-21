from os import environ
from typing import Any, Optional

import toml
from BL_Python.programming.collections.dict import AnyDict, merge
from flask.config import Config as FlaskAppConfig
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class LoggingConfig:
    log_level: str = "INFO"


@dataclass(frozen=True)
class FlaskOpenApiConfig:
    spec_path: str | None = None
    validate_responses: bool = False


@dataclass(frozen=True)
class FlaskSessionCookieConfig:
    secret_key: str = "abc123"
    httponly: bool = True
    secure: bool = True
    samesite: str = "None"

    def _prepare_env_for_flask(self):
        environ.update(
            {
                "SECRET_KEY": self.secret_key,
                "SESSION_COOKIE_HTTPONLY": str(1 if self.httponly else 0),
                "SESSION_COOKIE_SECURE": str(1 if self.secure else 0),
                "SESSION_COOKIE_SAMESITE": self.samesite,
            }
        )

    def _update_flask_config(self, flask_app_config: FlaskAppConfig):
        class ConfigObject:
            SECRET_KEY = self.secret_key
            SESSION_COOKIE_HTTPONLY = self.httponly
            SESSION_COOKIE_SECURE = self.secure
            SESSION_COOKIE_SAMESITE = self.samesite

        flask_app_config.from_object(ConfigObject)


@dataclass(frozen=True)
class FlaskSessionConfig:
    cookie: FlaskSessionCookieConfig
    permanent: bool = True
    lifetime: int | None = 86400
    refresh_each_request: bool = True

    def _prepare_env_for_flask(self):
        environ.update(
            {
                "PERMANENT_SESSION": str(1 if self.permanent else 0),
                "PERMANENT_SESSION_LIFETIME": str(self.lifetime)
                if self.lifetime
                else "",
                "SESSION_REFRESH_EACH_REQUEST": str(
                    1 if self.refresh_each_request else 0
                ),
            }
        )
        self.cookie._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]

    def _update_flask_config(self, flask_app_config: FlaskAppConfig):
        self.cookie._update_flask_config(  # pyright: ignore[reportPrivateUsage]
            flask_app_config
        )

        class ConfigObject:
            PERMANENT_SESSION = self.permanent
            PERMANENT_SESSION_LIFETIME = self.lifetime
            SESSION_REFRESH_EACH_REQUEST = self.refresh_each_request

        flask_app_config.from_object(ConfigObject)


@dataclass(frozen=True)
class FlaskConfig:
    app_name: str = "app"
    env: str = "Development"
    host: str | None = None
    port: str | None = None
    openapi: FlaskOpenApiConfig | None = None
    session: FlaskSessionConfig | None = None

    def _prepare_env_for_flask(self):
        environ.update({"ENV": self.env})
        if self.session:
            self.session._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]

    def _update_flask_config(self, flask_app_config: FlaskAppConfig):
        if self.session:
            self.session._update_flask_config(  # pyright: ignore[reportPrivateUsage]
                flask_app_config
            )

        class ConfigObject:
            ENV = self.env

        flask_app_config.from_object(ConfigObject)


@dataclass(frozen=True)
class DatabaseConfig:
    connection_string: str = "sqlite:///:memory:"
    sqlalchemy_echo: bool = False


@dataclass(frozen=True)
class SAML2Config:
    metadata: str | None = None
    metadata_url: str | None = None
    relay_state: str | None = None
    # TODO is there a more specific type than `Any`
    # that fits logging configurations?
    logging: dict[str, Any] | None = None


@dataclass(frozen=True)
class Config:
    logging: LoggingConfig = LoggingConfig()
    flask: FlaskConfig | None = None
    database: DatabaseConfig | None = None
    saml2: SAML2Config | None = None

    def prepare_env_for_flask(self):
        if self.flask:
            self.flask._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]

    def update_flask_config(self, flask_app_config: FlaskAppConfig):
        if self.flask:
            self.flask._update_flask_config(  # pyright: ignore[reportPrivateUsage]
                flask_app_config
            )


def load_config(toml_file_path: str, config_overrides: AnyDict | None = None):
    config_dict: dict[str, Any] = toml.load(toml_file_path)

    if config_overrides is not None:
        config_dict = merge(config_dict, config_overrides)

    config = Config(**config_dict)
    config.prepare_env_for_flask()
    return config
