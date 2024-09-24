from pathlib import Path

import pytest
from Ligare.database.migrations.alembic.env import run_migrations
from Ligare.programming.str import get_random_str
from mock import MagicMock
from pytest_mock import MockerFixture


def test__run_migrations__sets_default_config_filename(mocker: MockerFixture):
    _ = mocker.patch(
        "Ligare.database.migrations.alembic.env.get_database_config_container"
    )
    _ = mocker.patch("Ligare.database.migrations.alembic.env.load_config")
    _ = mocker.patch("Ligare.database.migrations.alembic.env.context")
    path_mock = mocker.patch("Ligare.database.migrations.alembic.env.Path")

    run_migrations(MagicMock())

    path_mock.assert_called_once_with("config.toml")


def test__run_migrations__uses_specified_config_filename(mocker: MockerFixture):
    _ = mocker.patch("Ligare.database.migrations.alembic.env.Path")
    _ = mocker.patch(
        "Ligare.database.migrations.alembic.env.get_database_config_container"
    )
    config_mock = mocker.patch("Ligare.database.migrations.alembic.env.Config")
    load_config_mock = mocker.patch(
        "Ligare.database.migrations.alembic.env.load_config"
    )
    _ = mocker.patch("Ligare.database.migrations.alembic.env.context")

    config_filename = Path(get_random_str())
    run_migrations(MagicMock(), config_filename=config_filename)

    load_config_mock.assert_called_once_with(config_mock, config_filename)


@pytest.mark.parametrize("mode", ["online", "offline"])
def test__run_migrations__runs_correct_migration_mode(mode: str, mocker: MockerFixture):
    _ = mocker.patch("Ligare.database.migrations.alembic.env.load_config")
    _ = mocker.patch("Ligare.database.migrations.alembic.env.Path")
    _ = mocker.patch(
        "Ligare.database.migrations.alembic.env.context",
        is_offline_mode=MagicMock(return_value=mode == "offline"),
    )
    alembic_env_setup_mock = MagicMock(
        run_migrations_offline=MagicMock(), run_migrations_online=MagicMock()
    )
    _ = mocker.patch(
        "Ligare.database.migrations.alembic.env.get_database_config_container",
        return_value=MagicMock(
            create_object=MagicMock(return_value=alembic_env_setup_mock)
        ),
    )

    _ = run_migrations(MagicMock())

    if mode == "offline":
        alembic_env_setup_mock.run_migrations_offline.assert_called_once()
    else:
        alembic_env_setup_mock.run_migrations_online.assert_called_once()
