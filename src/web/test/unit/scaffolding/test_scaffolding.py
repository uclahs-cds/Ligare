import logging

import pytest
from BL_Python.web.scaffolding.__main__ import (
    _parse_args,  # pyright: ignore[reportPrivateUsage]
)
from BL_Python.web.scaffolding.__main__ import (
    scaffold,  # pyright: ignore[reportUnusedImport]
)
from pytest import CaptureFixture, LogCaptureFixture


def test__parse_args__requires_run_mode_switch(capsys: CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        _ = _parse_args([])
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        "error: the following arguments are required: {create,modify}" in captured.err
    )


def test__parse_args__create_mode_requires_name(capsys: CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        _ = _parse_args(["create"])
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert "error: the following arguments are required: -n" in captured.err


def test__parse_args__modify_mode_requires_name(capsys: CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        _ = _parse_args(["modify"])
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert "error: the following arguments are required: -n" in captured.err


def test__parse_args__disallows_endpoints_named_application(
    caplog: LogCaptureFixture,
):
    with caplog.at_level(logging.DEBUG):
        # FIXME "Application" passes, but should it?
        args = _parse_args(["create", "-n", "test", "-e", "application"])

    assert (
        'The endpoint name "application" is reserved and will not be scaffolded.'
        in caplog.messages
    )
    assert "application" not in args.endpoints
