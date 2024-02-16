import logging
from dataclasses import asdict
from typing import Any, cast

import pytest
from BL_Python.web.scaffolding.__main__ import ScaffolderCli, scaffold
from BL_Python.web.scaffolding.scaffolder import (
    Operation,
    ScaffoldEndpoint,
    ScaffoldModule,
)
from pytest import CaptureFixture
from pytest_mock import MockerFixture

# pyright: reportPrivateUsage=false


@pytest.mark.parametrize(
    "name,expected_name",
    [
        ("foo", "foo"),
        ("FOO", "foo"),
        ("foo_bar", "foo_bar"),
        ("foo-bar", "foo_bar"),
        ("foo.bar", "foo_bar"),
        ("foo bar", "foo_bar"),
        ("foo0bar", "foo0bar"),
    ],
)
def test__operation__normalizes_module_name(name: str, expected_name: str):
    operation = Operation(name)
    assert expected_name == operation.module_name


@pytest.mark.parametrize(
    "name,expected_name",
    [
        ("foo", "foo"),
        ("FOO", "foo"),
        ("foo_bar", "foo_bar"),
        ("foo-bar", "foo-bar"),
        ("foo.bar", "foo.bar"),
        ("foo bar", "foo bar"),
        ("foo0bar", "foo0bar"),
    ],
)
def test__operation__normalizes_url_path_name(name: str, expected_name: str):
    operation = Operation(name)
    assert expected_name == operation.url_path_name


@pytest.mark.parametrize(
    "name",
    ["foo", "FOO", "foo_bar", "foo-bar", "foo.bar", "foo bar", "foo0bar"],
)
def test__operation__does_not_normalize_raw_name(name: str):
    operation = Operation(name)
    assert name == operation.raw_name


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


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__supports_specific_run_modes(mode: str):
    args = ScaffolderCli()._parse_args([mode, "-n", "test"])
    assert mode == args.mode


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__disallows_application_to_be_named_application(
    mode: str, capsys: CaptureFixture[str]
):
    with pytest.raises(SystemExit) as e:
        _ = ScaffolderCli()._parse_args([mode, "-n", "application"])

    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        "`application` is not an allowed value of the `name` argument." in captured.err
    )


@pytest.mark.parametrize(
    "mode,application_name,expected_url_path_name,expected_module_name",
    [
        ("create", "FOO", "foo", "foo"),
        ("create", "foo", "foo", "foo"),
        ("create", "FOO_BAR", "foo_bar", "foo_bar"),
        ("create", "FOO-BAR", "foo-bar", "foo_bar"),
        ("create", "FOO BAR", "foo bar", "foo_bar"),
        ("modify", "FOO", "foo", "foo"),
        ("modify", "foo", "foo", "foo"),
        ("modify", "FOO_BAR", "foo_bar", "foo_bar"),
        ("modify", "FOO-BAR", "foo-bar", "foo_bar"),
        ("modify", "FOO BAR", "foo bar", "foo_bar"),
    ],
)
def test__parse_args__normalizes_application_name(
    mode: str,
    application_name: str,
    expected_url_path_name: str,
    expected_module_name: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", application_name])

    assert args.name is not None
    assert expected_url_path_name == args.name.url_path_name
    assert expected_module_name == args.name.module_name


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__disallows_endpoints_named_application(
    mode: str, capsys: CaptureFixture[str]
):
    with pytest.raises(SystemExit) as e:
        _ = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", "application"])

    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        "`application` is not an allowed value of the `endpoint` argument."
        in captured.err
    )


@pytest.mark.parametrize(
    "mode,endpoint_name,expected_url_path_name,expected_module_name",
    [
        ("create", "FOO", "foo", "foo"),
        ("create", "foo", "foo", "foo"),
        ("create", "FOO_BAR", "foo_bar", "foo_bar"),
        ("create", "FOO-BAR", "foo-bar", "foo_bar"),
        ("create", "FOO BAR", "foo bar", "foo_bar"),
        ("modify", "FOO", "foo", "foo"),
        ("modify", "foo", "foo", "foo"),
        ("modify", "FOO_BAR", "foo_bar", "foo_bar"),
        ("modify", "FOO-BAR", "foo-bar", "foo_bar"),
        ("modify", "FOO BAR", "foo bar", "foo_bar"),
    ],
)
def test__parse_args__normalizes_endpoint_names(
    mode: str,
    endpoint_name: str,
    expected_url_path_name: str,
    expected_module_name: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", endpoint_name])

    assert args.endpoints is not None
    assert (expected_url_path_name, expected_module_name) in {
        (endpoint.url_path_name, endpoint.module_name) for endpoint in args.endpoints
    }


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__allows_multiple_endpoints(mode: str):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", "foo", "-e", "bar"])

    assert args.endpoints is not None
    endpoints = {
        (endpoint.url_path_name, endpoint.module_name) for endpoint in args.endpoints
    }
    assert ("foo", "foo") in endpoints
    assert ("bar", "bar") in endpoints


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__disallows_duplicated_endpoint_names(
    mode: str, capsys: CaptureFixture[str]
):
    with pytest.raises(SystemExit) as e:
        # foo-bar and foo_bar are normalized and are equivalent.
        # no need to duplicate the name normalization tests; just use the exact values here
        _ = ScaffolderCli()._parse_args(
            [mode, "-n", "test", "-e", "foo", "-e", "foo_bar", "-e", "foo-bar"]
        )
        # T
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        f"{mode}: error: argument -e: The ['-e'] argument does not allow duplicate values. The value `foo-bar` duplicates the value `foo_bar`."
        in captured.err
    )


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__disallows_endpoints_with_same_name_as_application(
    mode: str, capsys: CaptureFixture[str]
):
    with pytest.raises(SystemExit) as e:
        # foo-bar and foo_bar are normalized and are equivalent.
        # no need to duplicate the name normalization tests; just use the exact values here
        _ = ScaffolderCli()._parse_args([mode, "-n", "foo-bar", "-e", "foo_bar"])
    captured = capsys.readouterr()
    assert e.value.code == 2
    assert (
        f"{mode}: error: argument -e: The ['-e'] argument cannot be equivalent to the `name` argument. The value `foo_bar` is equivalent to the value `foo-bar`."
        in captured.err
    )


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__uses_application_name_for_endpoint_if_no_endpoints_given(
    mode: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test"])

    assert args.endpoints is not None
    assert ("test", "test") in {
        (endpoint.url_path_name, endpoint.module_name) for endpoint in args.endpoints
    }


@pytest.mark.parametrize("mode", ["create", "modify"])
def test__parse_args__does_not_use_application_name_for_endpoint_if_endpoints_given(
    mode: str,
):
    args = ScaffolderCli()._parse_args([mode, "-n", "test", "-e", "foo"])

    assert args.endpoints is not None
    endpoints = {
        (endpoint.url_path_name, endpoint.module_name) for endpoint in args.endpoints
    }

    assert ("test", "test") not in endpoints
    assert ("foo", "foo") in endpoints


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

    assert args.modules is not None
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


@pytest.mark.parametrize("env_log_level", [str(logging.DEBUG), str(logging.INFO)])
def test__scaffold__sets_log_level_from_envvar_when_parameter_not_specified(
    env_log_level: str,
    mocker: MockerFixture,
):
    scaffolder_cli_mock = mocker.patch(
        "BL_Python.web.scaffolding.__main__.ScaffolderCli"
    )
    environ_mock = mocker.patch(
        "BL_Python.web.scaffolding.__main__.environ.get",
        return_value=env_log_level,
    )

    scaffold()

    environ_mock.assert_called_once_with("LOG_LEVEL")
    scaffolder_cli_mock.assert_called_with(env_log_level)


@pytest.mark.parametrize("log_level", ["DEBUG", "debug", "10", 10])
def test__scaffold__sets_log_level_from_value_when_parameter_specified(
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


def test__scaffold__fails_when_log_level_is_any_unexpected_exception(
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
        ("create", "application.module_name", "test"),
        ("modify", "mode", "modify"),
        ("modify", "output_directory", "test"),
        ("modify", "application.module_name", "test"),
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

    config_name_parts = config_name.split(".")
    if len(config_name_parts) == 1:
        assert config_value == config[config_name_parts[0]]
    else:
        # tests `config['application']['module_name']`
        assert (
            config_value == asdict(config[config_name_parts[0]])[config_name_parts[1]]
        )


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
        endpoint.operation.url_path_name
        for endpoint in cast(
            list[ScaffoldEndpoint], config_mock.call_args.kwargs["endpoints"]
        )
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
        module.module_name
        for module in cast(
            list[ScaffoldModule], config_mock.call_args.kwargs["modules"]
        )
    ]

    assert "database" in module_names
