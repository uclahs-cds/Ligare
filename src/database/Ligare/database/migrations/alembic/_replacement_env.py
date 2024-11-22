"""
Alembic environment executor for scaffolded applications.
"""

from pathlib import Path

from alembic import context
from Ligare.database.migrations.alembic.env import run_migrations

# Only run migrations when this file is imported
# through Alembic at the command line.
if hasattr(context, "script"):
    # TODO replace with your MetaBase types and config file path
    run_migrations(bases=[], config_filename=Path("config.toml"))
