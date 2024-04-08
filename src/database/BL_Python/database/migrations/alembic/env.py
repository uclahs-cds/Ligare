from pathlib import Path

from alembic import context
from BL_Python.database.config import Config, DatabaseConfig
from BL_Python.database.migrations.alembic.env_setup import AlembicEnvSetup
from BL_Python.database.types import MetaBase
from BL_Python.programming.config import ConfigBuilder, load_config
from BL_Python.programming.dependency_injection import ConfigModule
from injector import Injector


def run_migrations(bases: list[MetaBase], config_filename: Path | None = None):
    if config_filename is None:
        config_filename = Path("config.toml")

    config_type = ConfigBuilder[Config]().with_root_config(Config).build()
    config = load_config(config_type, config_filename)
    config_module = ConfigModule(config, Config)
    database_config_module = ConfigModule(config.database, DatabaseConfig)

    ioc_container = Injector([config_module, database_config_module])

    alembic_env = ioc_container.create_object(AlembicEnvSetup)

    if context.is_offline_mode():
        alembic_env.run_migrations_offline(bases)
    else:
        alembic_env.run_migrations_online(bases)
