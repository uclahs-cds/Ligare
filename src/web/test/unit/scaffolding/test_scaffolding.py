import logging
from typing import Any

import pytest
from BL_Python.web.scaffolding.__main__ import ScaffolderCli, scaffold
from pytest import CaptureFixture, LogCaptureFixture
from pytest_mock import MockerFixture

# pyright: reportPrivateUsage=false


def test__parse_args__requires_run_mode_switch(capsys: CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        _ = ScaffolderCli()._parse_args([])
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        "error: the following arguments are required: {create,modify}" in captured.err
    )


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__modes_requires_name(mode: str, capsys: CaptureFixture[str]):
    with pytest.raises(SystemExit) as e:
        _ = ScaffolderCli()._parse_args([mode])
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert "error: the following arguments are required: -n" in captured.err


@pytest.mark.parametrize("mode_name", ["create", "modify"])
def test__parse_args__supports_specific_run_modes(mode_name: str):
    args = ScaffolderCli()._parse_args([mode_name, "-n", "test"])
    assert mode_name == args.mode


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__disallows_endpoints_named_application(
    mode: str,
    caplog: LogCaptureFixture,
):
    with caplog.at_level(logging.DEBUG):
        args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", "application"])

    assert (
        'The endpoint name "application" is reserved and will not be scaffolded.'
        in caplog.messages
    )
    assert "application" not in args.endpoints


@pytest.mark.parametrize(
    "mode,endpoint_name",
    [("create", "FOO"), ("create", "foo"), ("modify", "FOO"), ("modify", "foo")],
)
def test__parse_args__lowercases_endpoint_names(
    mode: str,
    endpoint_name: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", endpoint_name])

    assert endpoint_name.lower() in args.endpoints


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__allows_multiple_endpoints(mode: str):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", "foo", "-e", "bar"])

    assert "foo" in args.endpoints
    assert "bar" in args.endpoints


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__uses_application_name_for_endpoint_if_no_endpoints_given(
    mode: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test"])

    assert "test" in args.endpoints


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__does_not_use_application_name_if_endpoints_given(mode: str):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", "foo"])

    assert "test" not in args.endpoints


@pytest.mark.parametrize(
    "mode,template_type",
    [
        ("create", "basic"),
        ("create", "openapi"),
    ],
)
def test__parse_args__supports_specific_template_types(
    mode: str,
    template_type: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-t", template_type])

    assert template_type == args.template_type


@pytest.mark.parametrize(
    "mode,template_type",
    [
        ("create", "BASIC"),
        ("create", "basic"),
        ("create", "OPENAPI"),
        ("create", "openapi"),
    ],
)
def test__parse_args__lowercases_template_type(
    mode: str,
    template_type: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-t", template_type])

    assert template_type.lower() == args.template_type


@pytest.mark.parametrize("mode,module_name", [("create", "database")])
def test__parse_args__supports_specific_modules(
    mode: str,
    module_name: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-m", module_name])

    assert module_name in args.modules


@pytest.mark.parametrize("mode,module_name", [("create", "DATABASE")])
def test__parse_args__does_not_lowercase_modules(
    mode: str, module_name: str, capsys: CaptureFixture[str]
):
    with pytest.raises(SystemExit) as e:
        _ = ScaffolderCli()._parse_args([mode, "-n", "test", "-m", module_name])

    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        f"{mode}: error: argument -m: invalid choice: 'DATABASE' (choose from 'database')"
        in captured.err
    )


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__supports_setting_explicit_output_directory(mode: str):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-o", "output_dir"])

    assert "output_dir" == args.output_directory


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__uses_application_name_for_output_directory_if_no_outout_directory_given(
    mode: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test"])

    assert "test" == args.output_directory


def test__scaffold__sets_log_level_from_envvar_when_not_specified(
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.ScaffolderCli.run")
    environ_mock = mocker.patch(
        "BL_Python.web.scaffolding.__main__.environ.get", return_value=logging.DEBUG
    )

    scaffold()

    environ_mock.assert_called_once_with("LOG_LEVEL")


@pytest.mark.parametrize("log_level", ["DEBUG", "debug", "10", 10])
def test__scaffold__sets_log_level_from_value(
    log_level: str | int, mocker: MockerFixture
):
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.ScaffolderCli.run")
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.environ")

    log_mock = mocker.patch("BL_Python.web.scaffolding.__main__.logging.basicConfig")

    expected_log_level = 10
    scaffold(log_level=log_level)

    log_mock.assert_called()
    for call_args in log_mock.call_args:
        if not isinstance(call_args, dict):
            continue
        assert "level" in call_args
        assert expected_log_level == call_args["level"]


@pytest.mark.parametrize("exception_type", [Exception, ValueError, TypeError])
def test__scaffold__fails_when_log_level_is_any_unexpected_exception(
    exception_type: type[Exception],
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.ScaffolderCli.run")

    def fake_exception(*args: Any, **kwargs: Any):
        raise ValueError("fake exception")

    _ = mocker.patch(
        "BL_Python.web.scaffolding.__main__.int", side_effect=fake_exception
    )

    with pytest.raises(ValueError, match=r"^fake exception$"):
        scaffold(log_level="x")


def test__scaffold__uses_sys_argv_when_args_not_given(mocker: MockerFixture):
    scaffolder_cli = mocker.patch(
        "BL_Python.web.scaffolding.__main__.ScaffolderCli.run"
    )
    argv_values = ["1", "2", "3"]
    argv = mocker.patch("BL_Python.web.scaffolding.__main__.sys.argv")
    argv.__getitem__ = (
        lambda _argv, _slice: argv_values  # pyright: ignore[reportUnknownLambdaType]
    )

    scaffold()

    scaffolder_cli.assert_called_with(argv_values)


def test__scaffold__uses_argv_when_sys_argv_not_set(mocker: MockerFixture):
    scaffolder_cli = mocker.patch(
        "BL_Python.web.scaffolding.__main__.ScaffolderCli.run"
    )
    argv_values = ["1", "2", "3"]

    scaffold(argv_values)

    scaffolder_cli.assert_called_with(argv_values)


@pytest.mark.parametrize(
    "mode,config_name,config_value",
    [
        ("create", "mode", "create"),
        ("create", "template_type", "basic"),
        ("create", "output_directory", "test"),
        ("create", "application_name", "test"),
        ("modify", "mode", "modify"),
        ("modify", "output_directory", "test"),
        ("modify", "application_name", "test"),
    ],
)
def test__scaffold__uses_argv_for_basic_scaffold_configuration(
    mode: str, config_name: str, config_value: str, mocker: MockerFixture
):
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.Scaffolder")
    config_mock = mocker.patch("BL_Python.web.scaffolding.__main__.ScaffoldConfig")

    argv_values = [mode, "-n", "test"]

    scaffold(argv_values)

    config = config_mock.call_args.kwargs

    assert config_value == config[config_name]

    pass


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__scaffold__uses_argv_for_endpoint_configuration(
    mode: str,
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.Scaffolder")
    config_mock = mocker.patch("BL_Python.web.scaffolding.__main__.ScaffoldConfig")

    argv_values = [mode, "-n", "test", "-e", "foo", "-e", "bar"]

    scaffold(argv_values)

    endpoint_names = [
        endpoint.endpoint_name for endpoint in config_mock.call_args.kwargs["endpoints"]
    ]

    assert "foo" in endpoint_names
    assert "bar" in endpoint_names


def test__scaffold__create_mode_uses_argv_for_module_configuration(
    mocker: MockerFixture,
):
    _ = mocker.patch("BL_Python.web.scaffolding.__main__.Scaffolder")
    config_mock = mocker.patch("BL_Python.web.scaffolding.__main__.ScaffoldConfig")

    argv_values = ["create", "-n", "test", "-m", "database"]

    scaffold(argv_values)

    module_names = [
        module.module_name for module in config_mock.call_args.kwargs["modules"]
    ]

    assert "database" in module_names
