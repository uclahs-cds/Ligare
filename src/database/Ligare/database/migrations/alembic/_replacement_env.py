from pathlib import Path

from Ligare.database.migrations.alembic.env import run_migrations

# TODO replace with your MetaBase types and config file path
run_migrations(bases=[], config_filename=Path("config.toml"))
