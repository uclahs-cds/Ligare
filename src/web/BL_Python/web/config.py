"""
Flask configuration classes.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from os import environ
from pathlib import Path
from typing import Any, Optional

import flask
from click import Option
from dotenv import load_dotenv


@dataclass
class LoggingConfig:
    version: int
    formatters: dict[str, dict[str, str]]
    handlers: dict[str, dict[str, str]]
    loggers: dict[str, dict[str, str]]
    root: dict[str, str | list[str]]


# TODO determine whether this makes sense to keep in the BL_Python library
DEFAULT_ENV_FILE_SEARCH_PATH = "."


class Config(dict[str, Any]):
    """
    Base config file.
    """

    @staticmethod
    def from_env(
        environment_name: Optional[str] = None,
        env_file_search_path: str = DEFAULT_ENV_FILE_SEARCH_PATH,
    ):
        """
        Get a Config initialized with the values from a .env file.
        environment_name can be None, "production," "test," or "development."
        If environment_name is None, the environment variable "ENV" will be used
        to determine the environment_name. If "ENV" is not set, environment_name
        defaults to "production."
        """
        Config.initialize_env(env_file_search_path)

        if environment_name is None:
            environment_name = environ.get("ENV") or environ.get("FLASK_ENV")

        return (
            Config.get_env_config(environment_name)
            if environment_name
            else Config.get_env_config()
        )

    @staticmethod
    def initialize_env(search_path: str = DEFAULT_ENV_FILE_SEARCH_PATH):
        """
        Find a .env file within the specified path tree.
        Every path, including the root if starting with a "/", will be searched for a .env file.
        The first instance of a .env found will be ingested.
        """
        env_file_exists = False
        env_file_dir = Path()
        env_file_path = env_file_dir
        parts = search_path.split("/")
        for dir in parts:
            env_file_dir = env_file_dir.joinpath(dir)
            env_file_path = env_file_dir.joinpath(".env")
            if env_file_path.exists():
                env_file_exists = True
                load_dotenv(env_file_path, override=False)

        if not env_file_exists:
            logging.info(
                f'.env file was not found at "{env_file_path}". Not trying another path. If required environment \
        variables are not set, Flask will fail to run. To avoid this, either set the required environment variables \
        before executing Flask, or create a .env file with their values.'
            )

    @staticmethod
    def get_env_config(environment_name: str | None = "production"):
        """
        Get the correct config object based on the environment name.
        Can be either "development," "test," or "production"
        """
        if environment_name is None:
            environment_name = "production"
        # fmt: off
        if environment_name == "development": return DevelopmentConfig({})
        if environment_name == "test": return TestConfig({})
        if environment_name == "production": return ProductionConfig({})
        raise Exception(f'Unknown ENV "{environment_name}"')
        # fmt: on

    def apply(self, flask_config: flask.config.Config):
        # TODO apply the properties of the Config class to the Flask config
        pass

    def __init__(self, root_path: Any = None, defaults: Any | None = None) -> None:
        if root_path is None:
            root_path = {}
        # FIXME this was necessary when Config extended flask.config.Config
        # which is no longer necessary. Should this still run in the
        # self.apply(...) method?
        # super().__init__(root_path, defaults)

    DEBUG: bool = False
    TESTING: bool = False

    @property
    def FLASK_APP(self) -> Optional[str]:
        return environ.get("FLASK_APP")

    @property
    def OPENAPI_SPEC_PATH(self) -> Optional[str]:
        return environ.get("OPENAPI_SPEC_PATH")

    # The following can be set in environmant variables, or in .env
    @property
    def DATABASE_CONNECTION_STRING(self) -> Optional[str]:
        return environ.get("DATABASE_CONNECTION_STRING")

    @property
    def VALIDATE_API_RESPONSES(self) -> Optional[bool]:
        value = environ.get("VALIDATE_API_RESPONSES")
        return value == "True" or value == "1"

    @property
    def SAML2_METADATA_URL(self) -> Optional[str]:
        return environ.get("SAML2_METADATA_URL")

    @property
    def SAML2_METADATA(self) -> Optional[str]:
        saml2_metadata = environ.get("SAML2_METADATA")
        if saml2_metadata:
            # if SAML2_METADATA is set, because the envvar needs a single line,
            # the escaped `\n` characters in the value need to be replaced
            # with actual new line characters.
            return saml2_metadata.replace("\\n", "\n")

    @property
    def SAML2_RELAY_STATE(self) -> Optional[str]:
        return environ.get("SAML2_RELAY_STATE")

    # TODO determine how much this config should be aware of.
    # the BL_Python.web library does not depend on SQLAlchemy
    # so this config may not make sense.
    # Should we work on a way to extend configs from the other
    # libraries?
    @property
    def SQLALCHEMY_ECHO(self) -> bool:
        value = environ.get("SQLALCHEMY_ECHO")
        return value == "True" or value == "1"

    @property
    def PERMANENT_SESSION(self) -> bool:
        value = environ.get("PERMANENT_SESSION")
        return value == "True" or value == "1"

    @property
    def PERMANENT_SESSION_LIFETIME(self):
        seconds = int(
            environ.get("PERMANENT_SESSION_LIFETIME") or 86400  # default to 24 hour
        )
        return timedelta(seconds=seconds)

    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "None"

    @property
    def SECRET_KEY(self) -> Optional[str]:
        return environ.get("FLASK_SECRET_KEY")

    # TODO this can be replaced by Python's logging config.
    # First, we need to reconcile different log handlers (gunicorn, flask, stdout)
    # and how/where the logs for each are output and any other related configs.
    SAML2_LOGGING = LoggingConfig(
        version=1,
        formatters={
            "simple": {
                "format": "[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s] %(message)s",
            }
        },
        handlers={
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "level": "DEBUG",
                "formatter": "simple",
            }
        },
        loggers={
            "saml2": {"level": "DEBUG"},
        },
        root={
            "level": "DEBUG",
            "handlers": [
                "stdout",
            ],
        },
    )


class ProductionConfig(Config):
    """
    Production config file.
    """

    DEBUG = False

    @property
    def SECRET_KEY(self) -> str:
        secret_key = environ.get("FLASK_SECRET_KEY")
        assert secret_key is not None, "FLASK_SECRET_KEY must be set in Production"
        assert len(secret_key) > 0, "FLASK_SECRET_KEY must not be empty in Production"
        return secret_key


class DevelopmentConfig(Config):
    """
    Development config file.
    """

    DEBUG = True

    @property
    def DATABASE_CONNECTION_STRING(self) -> str:
        return environ.get("DATABASE_CONNECTION_STRING") or "sqlite:///.app.db"

    @property
    def SAML2_METADATA_URL(self) -> Optional[str]:
        return environ.get("SAML2_METADATA_URL")

    @property
    def SAML2_METADATA(self) -> Optional[str]:
        return super(DevelopmentConfig, self).SAML2_METADATA

    @property
    def SAML2_RELAY_STATE(self) -> Optional[str]:
        return environ.get("SAML2_RELAY_STATE") or "http://localhost:5000"


class TestConfig(Config):
    """
    Test config file.
    """

    DEBUG = True
    TESTING = True

    @property
    def DATABASE_CONNECTION_STRING(self):
        envvar_value = environ.get("DATABASE_CONNECTION_STRING")
        # If the connection string envvar is any kind of
        # in-memory sqlite database connection string, then use that value.
        # Otherwise, force an unnamed in-memory connection string.
        if (
            envvar_value is not None
            and envvar_value.startswith("sqlite")
            and ("mode=memory" in envvar_value or "/:memory:" in envvar_value)
        ):
            return envvar_value

        return "sqlite:///:memory:"
