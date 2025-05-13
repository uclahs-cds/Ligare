import pytest
from Ligare.programming.R.exception import RscriptProcessError, RscriptScriptError
from Ligare.programming.R.process import RProcessStepBuilder
from mock import MagicMock
from pytest_mock import MockerFixture


def test__RProcessStepBuilder__ScriptStepBuilder_parent_is_ProcessStepBuilder():
    builder = RProcessStepBuilder()
    script_builder = builder.with_Rscript_binary_path("")
    assert script_builder.process == builder


def test__RProcessScriptStepBuilder__MethodStepBuilder_parent_is_ScriptStepBuilder():
    builder = RProcessStepBuilder()
    script_builder = builder.with_Rscript_binary_path("")
    method_builder = script_builder.with_R_script_path("")
    assert method_builder.script == script_builder


def test__RProcessMethodStepBuilder__ExecutorStepBuilder_parent_is_MethodStepBuilder():
    builder = RProcessStepBuilder()
    script_builder = builder.with_Rscript_binary_path("")
    method_builder = script_builder.with_R_script_path("")
    executor_builder = method_builder.with_data(b"")
    assert executor_builder.method == method_builder


def test__RProcessStepBuilder__execute_does_not_require_method_parameters(
    mocker: MockerFixture,
):
    run_mock = MagicMock(return_value=MagicMock(stdout=b"foo", returncode=0))
    _ = mocker.patch("Ligare.programming.R.process.subprocess", run=run_mock)
    executor = (
        RProcessStepBuilder()
        .with_Rscript_binary_path("")
        .with_R_script_path("")
        .with_data(b"")
    )
    _ = executor.execute()
    run_mock.assert_called_once()


def test__RProcessStepBuilder__execute_uses_correct_command(
    mocker: MockerFixture,
):
    run_mock = MagicMock(return_value=MagicMock(stdout=b"foo", returncode=0))
    _ = mocker.patch("Ligare.programming.R.process.subprocess", run=run_mock)
    binary_path = "/bin"
    script_path = "foo.R"
    executor = (
        RProcessStepBuilder()
        .with_Rscript_binary_path(binary_path)
        .with_R_script_path(script_path)
        .with_data(b"")
    )
    _ = executor.execute()
    run_mock.assert_called_once()
    assert run_mock.call_args[0] == ([binary_path, script_path],)


def test__RProcessStepBuilder__execute_uses_method_parameters(
    mocker: MockerFixture,
):
    run_mock = MagicMock(return_value=MagicMock(stdout=b"foo", returncode=0))
    _ = mocker.patch("Ligare.programming.R.process.subprocess", run=run_mock)
    _ = mocker.patch("Ligare.programming.R.process.pipe", return_value=(123, 456))
    _ = mocker.patch("Ligare.programming.R.process.open")
    _ = mocker.patch("Ligare.programming.R.process.os")
    writerow_mock = MagicMock()
    _ = mocker.patch(
        "Ligare.programming.R.process.csv",
        DictWriter=MagicMock(return_value=MagicMock(writerow=writerow_mock)),
    )
    method_parameters = {"foo": "bar"}
    executor = (
        RProcessStepBuilder()
        .with_Rscript_binary_path("")
        .with_R_script_path("")
        .with_method_parameters(method_parameters)
        .with_data(b"")
    )
    _ = executor.execute()
    writerow_mock.assert_called_once()
    writerow_mock.call_args[0][0]
    assert "foo" in writerow_mock.call_args[0][0]
    assert writerow_mock.call_args[0][0]["foo"] == "bar"


def test__RProcessStepBuilder__raises_RscriptProcessError_when_Rscript_errors(
    mocker: MockerFixture,
):
    # When `Rscript` errors it:
    # returns > 0; writes to STDOUT; does not write to STDERR
    run_mock = MagicMock(
        return_value=MagicMock(stdout=b"foo", stderr=b"", returncode=1)
    )
    _ = mocker.patch("Ligare.programming.R.process.subprocess", run=run_mock)
    executor = (
        RProcessStepBuilder()
        .with_Rscript_binary_path("")
        .with_R_script_path("")
        .with_data(b"")
    )

    with pytest.raises(RscriptProcessError) as e:
        _ = executor.execute()

    assert e.value.proc.stdout == b"foo"
    assert str(e.value) == "foo"


def test__RProcessStepBuilder__raises_RscriptProcessError_when_Rscript_script_errors(
    mocker: MockerFixture,
):
    # When a script that `Rscript` executes errors, it:
    # returns > 0; writes to STDERR; maybe writes to STDOUT
    run_mock = MagicMock(
        return_value=MagicMock(stdout=b"", stderr=b"foo", returncode=1)
    )
    _ = mocker.patch("Ligare.programming.R.process.subprocess", run=run_mock)
    executor = (
        RProcessStepBuilder()
        .with_Rscript_binary_path("")
        .with_R_script_path("")
        .with_data(b"")
    )

    with pytest.raises(RscriptScriptError) as e:
        _ = executor.execute()

    assert e.value.proc.stderr == b"foo"
    assert str(e.value) == "foo"
