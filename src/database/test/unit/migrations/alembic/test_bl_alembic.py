from typing import Any, Generator, Protocol
from unittest.mock import MagicMock

import alembic
import alembic.util
import pytest
from BL_Python.database.migrations.alembic.bl_alembic import BLAlembic
from mock import MagicMock
from pytest_mock import MockerFixture
from pytest_mock.plugin import MockType


class MockArgv(Protocol):
    def __call__(self, args: list[str]) -> MockType: ...


@pytest.fixture
def mock_argv(mocker: MockerFixture) -> Generator[MockArgv, Any, None]:
    argv = mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.sys.argv")

    def set_args(args: list[str]):
        argv.__getitem__ = (
            lambda _argv, _slice: (["bl-alembic"] + args)[_slice]  # pyright: ignore[reportUnknownLambdaType]
        )
        return argv

    yield set_args


def mock_alembic(mocker: MockerFixture):
    return mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.alembic_main")


def mock_config(mocker: MockerFixture):
    return mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.Config")


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["-h"],
        ["--help"],
        ["-c", "test-config.ini"],
        ["--config", "test-config.ini"],
        ["-c", "alembic.ini", "upgrade", "head"],
    ],
)
def test__BLAlembic__passes_through_to_alembic_with_correct_args(
    args: list[str], mock_argv: MockArgv, mocker: MockerFixture
):
    _ = mock_argv(args)
    _ = mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.Config")
    alembic_main = mocker.patch(
        "BL_Python.database.migrations.alembic.bl_alembic.alembic_main"
    )

    bl_alembic = BLAlembic(None, MagicMock())
    bl_alembic.run()

    assert alembic_main.called
    alembic_main.assert_called_once_with(args)


def test__BLAlembic__passes_through_to_alembic_with_default_config_when_not_specified(
    mock_argv: MockArgv,
    mocker: MockerFixture,
):
    args = ["upgrade", "head"]
    _ = mock_argv(args)
    _ = mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.Config")
    alembic_main = mocker.patch(
        "BL_Python.database.migrations.alembic.bl_alembic.alembic_main"
    )

    bl_alembic = BLAlembic(None, MagicMock())
    bl_alembic.run()

    assert alembic_main.called
    alembic_main.assert_called_once_with(["-c", BLAlembic.DEFAULT_CONFIG_NAME] + args)


def test__BLAlembic__creates_default_config(mock_argv: MockArgv, mocker: MockerFixture):
    _ = mock_alembic(mocker)
    _ = mock_config(mocker)
    _ = mock_argv(["upgrade", "head"])

    def path_se(*args: Any, **kwargs: Any):
        # set the call args for the Path mocks that are passed
        # into the FileCopy mock so we can examine them when FileCopy
        # is called
        return MagicMock(args=args)

    def file_copy_se(*args: Any, **kwargs: Any):
        # set a mocked FileCopy whose src/dest are strings (filenames)
        return MagicMock(source=args[0].args[1], destination=args[1].args[1])

    _ = mocker.patch(
        "BL_Python.database.migrations.alembic.bl_alembic.Path", side_effect=path_se
    )
    _ = mocker.patch(
        "BL_Python.database.migrations.alembic.bl_alembic.BLAlembic.FileCopy",
        side_effect=file_copy_se,
    )
    open_mock = mocker.patch("builtins.open", mocker.mock_open())

    bl_alembic = BLAlembic(None, MagicMock())
    bl_alembic.run()

    assert open_mock.called
    call_args = [call[0] for call in open_mock.call_args_list]
    assert (BLAlembic.DEFAULT_CONFIG_NAME, "r") in call_args
    assert (BLAlembic.DEFAULT_CONFIG_NAME, "x+b") in call_args


def test__BLAlembic__does_not_overwrite_existing_config(
    mock_argv: MockArgv, mocker: MockerFixture
):
    _ = mock_alembic(mocker)
    _ = mock_argv(["upgrade", "head"])

    _ = mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.Path")
    open_mock = mocker.patch("builtins.open", mocker.mock_open())

    def raise_file_exists_error(*args: Any, **kwargs: Any):
        raise FileExistsError()

    open_mock.side_effect = raise_file_exists_error

    with pytest.raises(FileExistsError):
        bl_alembic = BLAlembic(None, MagicMock())
        bl_alembic.run()


def test__BLAlembic__initializes_alembic_if_not_already_initialized(
    mock_argv: MockArgv, mocker: MockerFixture
):
    _ = mock_argv(["upgrade", "head"])

    _ = mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.Path")
    _ = mocker.patch("builtins.open", mocker.mock_open())

    _ = mock_config(mocker)
    _mock_alembic = mock_alembic(mocker)

    def write_init_message(*args: Any, **kwargs: Any):
        _mock_alembic.side_effect = None
        alembic.util.messaging.msg(
            "use the 'init' command to create a new scripts folder"
        )

    _mock_alembic.side_effect = write_init_message

    bl_alembic = BLAlembic(None, MagicMock())
    bl_alembic.run()

    assert "init" in [call[0][0][0] for call in _mock_alembic.call_args_list]


def test__BLAlembic__initializes_alembic_into_correct_directory_if_not_already_initialized(
    mock_argv: MockArgv, mocker: MockerFixture
):
    _ = mock_argv(["upgrade", "head"])

    _ = mocker.patch("BL_Python.database.migrations.alembic.bl_alembic.Path")
    _ = mocker.patch("builtins.open", mocker.mock_open())
    _mock_alembic = mock_alembic(mocker)

    # get_main_option_mock = MagicMock()
    def get_main_option(option: str):
        if option == "script_location":
            return "migrations/"
        return MagicMock()

    _ = mocker.patch(
        "BL_Python.database.migrations.alembic.bl_alembic.Config",
        return_value=MagicMock(get_main_option=get_main_option),
    )

    def write_init_message(*args: Any, **kwargs: Any):
        _mock_alembic.side_effect = None
        alembic.util.messaging.msg(
            "use the 'init' command to create a new scripts folder"
        )

    _mock_alembic.side_effect = write_init_message

    bl_alembic = BLAlembic(None, MagicMock())
    bl_alembic.run()

    assert ["init", "migrations/"] in [
        call[0][0] for call in _mock_alembic.call_args_list
    ]
