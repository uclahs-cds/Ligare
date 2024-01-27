from dataclasses import field
from os import environ
from typing import Any, Literal

from flask.config import Config as FlaskAppConfig
from pydantic import BaseModel


class LoggingConfig(BaseModel):
    log_level: str = "INFO"
    format: Literal["plaintext", "JSON"] = "JSON"


class WebSecurityCorsConfig(BaseModel):
    origin: str | None = None
    allow_credentials: bool = True
    allow_methods: list[
        Literal[
            "GET",
            "POST",
            "PATCH",
            "PUT",
            "DELETE",
            "OPTIONS",
            "HEAD",
            "CONNECT",
            "TRACE",
        ]
    ] = field(default_factory=lambda: ["GET", "POST", "OPTIONS"])


class WebSecurityConfig(BaseModel):
    cors: WebSecurityCorsConfig = WebSecurityCorsConfig()
    csp: str | None = None


class WebConfig(BaseModel):
    security: WebSecurityConfig = WebSecurityConfig()


class FlaskOpenApiConfig(BaseModel):
    spec_path: str | None = None
    validate_responses: bool = False
    use_swagger: bool = True
    swagger_url: str | None = None


class FlaskSessionCookieConfig(BaseModel):
    # FIXME this needs to be handled much more securely.
    # FIXME This is not done at the moment solely because we are not making
    # FIXME active use of sessions, but this should not be forgotten!
    secret_key: str | None = None
    name: str = "session"
    httponly: bool = True
    secure: bool = True
    samesite: str = "none"

    def _prepare_env_for_flask(self):
        if not self.secret_key:
            raise Exception("`flask.session.cookie.secret_key` must be set in config.")

        environ.update(
            {
                "SECRET_KEY": self.secret_key,
                "SESSION_COOKIE_NAME": self.name,
                "SESSION_COOKIE_HTTPONLY": str(1 if self.httponly else 0),
                "SESSION_COOKIE_SECURE": str(1 if self.secure else 0),
                "SESSION_COOKIE_SAMESITE": self.samesite,
            }
        )

    def _update_flask_config(self, flask_app_config: FlaskAppConfig):
        class ConfigObject:
            SECRET_KEY = self.secret_key
            SESSION_COOKIE_NAME = self.name
            SESSION_COOKIE_HTTPONLY = self.httponly
            SESSION_COOKIE_SECURE = self.secure
            SESSION_COOKIE_SAMESITE = self.samesite

        flask_app_config.from_object(ConfigObject)


class FlaskSessionConfig(BaseModel):
    cookie: FlaskSessionCookieConfig
    permanent: bool = True
    lifetime: int | None = 86400
    refresh_each_request: bool = True

    def _prepare_env_for_flask(self):
        environ.update(
            {
                "PERMANENT_SESSION": str(1 if self.permanent else 0),
                "PERMANENT_SESSION_LIFETIME": (
                    str(self.lifetime) if self.lifetime else ""
                ),
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


class FlaskConfig(BaseModel):
    app_name: str = "app"
    env: str = "Development"
    host: str = "localhost"
    port: str = "5000"
    openapi: FlaskOpenApiConfig | None = None
    session: FlaskSessionConfig | None = None

    def _prepare_env_for_flask(self):
        environ.update(
            FLASK_APP=self.app_name,
            ENV=self.env,
            FLASK_RUN_PORT=self.port,
            FLASK_RUN_HOST=self.host,
        )
        if self.session:
            self.session._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]

    def _update_flask_config(self, flask_app_config: FlaskAppConfig):
        if self.session:
            self.session._update_flask_config(  # pyright: ignore[reportPrivateUsage]
                flask_app_config
            )

        class ConfigObject:
            FLASK_APP = self.app_name
            ENV = self.env
            SERVER_NAME = f"{self.host}:{self.port}"
            FLASK_RUN_PORT = self.port
            FLASK_RUN_HOST = self.host
            TESTING = self.env == "Testing"

        flask_app_config.from_object(ConfigObject)


class SAML2Config(BaseModel):
    metadata: str | None = None
    metadata_url: str | None = None
    relay_state: str | None = None
    # TODO is there a more specific type than `Any`
    # that fits logging configurations?
    logging: dict[str, Any] | None = None


from BL_Python.programming.config import AbstractConfig


class Config(BaseModel, AbstractConfig):
    logging: LoggingConfig = LoggingConfig()
    web: WebConfig = WebConfig()
    flask: FlaskConfig | None = None

    def prepare_env_for_flask(self):
        if self.flask:
            self.flask._prepare_env_for_flask()  # pyright: ignore[reportPrivateUsage]

    def update_flask_config(self, flask_app_config: FlaskAppConfig):
        if self.flask:
            self.flask._update_flask_config(  # pyright: ignore[reportPrivateUsage]
                flask_app_config
            )
