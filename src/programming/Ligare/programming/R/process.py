import csv
import os
import subprocess
from logging import Logger
from os import PathLike, memfd_create, pipe
from typing import Any, Mapping, cast, final

from Ligare.programming.collections.dict import merge
from Ligare.programming.R.exception import RscriptProcessError, RscriptScriptError
from typing_extensions import Self

_path_like = str | bytes | PathLike[str] | PathLike[bytes]


@final
class RProcessStepBuilder:
    """
    Configure an object to execute an R script with Rscript.
    """

    def __init__(self, log: Logger | None = None) -> None:
        self._log = log

        self._rscript_path = None

    def with_log(self, log: Logger) -> Self:
        """
        Configure the logger.

        :param Logger log:
        :return Self:
        """
        self._log = log
        return self

    def with_Rscript_binary_path(
        self, rscript_path: _path_like
    ) -> "RProcessStepBuilder.RProcessScriptStepBuilder":
        """
        The path to the Rscript binary.

        :param _path_like rscript_path: The Rscript binary path
        :return RProcessStepBuilder.RProcessScriptStepBuilder: The next step for configuration
        """
        self._rscript_path = rscript_path
        return RProcessStepBuilder.RProcessScriptStepBuilder(self, self._log)

    def _build(self):
        if self._rscript_path is None:
            raise ValueError(
                f"The `Rscript` command path was not set with `{RProcessStepBuilder.with_Rscript_binary_path.__name__}`."
            )

    @final
    class RProcessScriptStepBuilder:
        """
        Configure the R script to execute with Rscript.
        """

        def __init__(self, parent: "RProcessStepBuilder", log: Logger | None = None):
            self._process = parent
            self._log = log

            self._args = []
            self._rscript = None

        def with_log(self, log: Logger) -> "Self":
            """
            Configure the logger.

            :param Logger log:
            :return Self:
            """
            self._log = log
            return self

        def with_args(self, args: list[str]):
            self._args = args
            return self

        def with_R_script_path(
            self, rscript: _path_like
        ) -> "RProcessStepBuilder.RProcessMethodStepBuilder":
            """
            The path to the R script to execute with Rscript

            :param _path_like rscript: The script path
            :return RProcessStepBuilder.RProcessMethodStepBuilder: The next step for configuration
            """
            self._rscript = rscript
            method_parameter_builder = RProcessStepBuilder.RProcessMethodStepBuilder(
                self, self._log
            )
            return method_parameter_builder

        @property
        def process(self) -> "RProcessStepBuilder":
            return self._process

        def _build(self) -> None:
            errors: list[Exception] = []
            if self._rscript is None:
                errors.append(
                    ValueError(
                        f"An R script path was not specified with `{RProcessStepBuilder.RProcessScriptStepBuilder.with_R_script_path.__name__}`"
                    )
                )

            try:
                self.process._build()
            except Exception as e:
                raise Exception(errors) from e

    # with_other_args? since args was just a list of the rscript bin executable and the script to execute
    # maybe we need to support passing other args
    @final
    class RProcessMethodStepBuilder:
        """
        Configure method parameters and input for the R script to read.
        """

        def __init__(
            self,
            parent: "RProcessStepBuilder.RProcessScriptStepBuilder",
            log: Logger | None = None,
        ):
            self._script = parent
            self._log = log
            self._method_parameters = None
            self._read_fd: int | None = None
            self._write_fd: int | None = None

            self._data = None
            self._executor = None

        def with_log(self, log: Logger) -> Self:
            """
            Configure the logger.

            :param Logger log:
            :return Self:
            """
            self._log = log
            return self

        def with_method_parameters(self, parameters: dict[str, Any]) -> Self:
            """
            The method parameters and their values.

            :param dict[str, Any] parameters: The parameters
            :return Self:
            """
            self._method_parameters = parameters
            return self

        def with_data(
            self, data: bytes
        ) -> "RProcessStepBuilder.RProcessExecutorStepBuilder":
            """
            The input data for the R script.

            :param bytes data: The data
            :return RProcessStepBuilder.RProcessExecutorStepBuilder: The next step for configuration
            """
            self._data = data
            self._executor = RProcessStepBuilder.RProcessExecutorStepBuilder(
                self, self._log
            )
            return self._executor

        @property
        def script(self) -> "RProcessStepBuilder.RProcessScriptStepBuilder":
            return self._script

        @staticmethod
        def write_method_parameters(parameters: dict[str, Any]) -> tuple[int, int]:
            """
            Open a FIFO pipe and write the dictionary `parameters` as a CSV to `write_fd`.

            :param dict[str, Any] parameters: The parameters to write to the pipe
            :return tuple[int, int]: (read_fd, write_fd) the input/output file descriptors of the pipe
            """
            read_fd, write_fd = pipe()

            with open(write_fd, "w") as f:
                csv_writer = csv.DictWriter(f, parameters.keys())
                csv_writer.writeheader()
                csv_writer.writerow(parameters)
                f.flush()

            return (read_fd, write_fd)

        def _build(self) -> None:
            This = RProcessStepBuilder.RProcessMethodStepBuilder

            self.script._build()  # pyright: ignore[reportPrivateUsage]

            if self._method_parameters is not None:
                self._read_fd, self._write_fd = This.write_method_parameters(
                    self._method_parameters
                )

    @final
    class RProcessExecutorStepBuilder:
        """
        The final step in configurating an R process executor.
        This class can run the command with the `execute()` method.
        """

        def __init__(
            self,
            parent: "RProcessStepBuilder.RProcessMethodStepBuilder",
            log: Logger | None = None,
        ):
            self._method = parent
            self._script = self._method.script
            self._process = self._script.process
            self._log = log

        def with_log(self, log: Logger) -> Self:
            """
            Configure the logger.

            :param Logger log:
            :return Self:
            """
            self._log = log
            return self

        @property
        def method(self) -> "RProcessStepBuilder.RProcessMethodStepBuilder":
            return self._method

        @property
        def script(self) -> "RProcessStepBuilder.RProcessScriptStepBuilder":
            return self._script

        @property
        def process(self) -> "RProcessStepBuilder":
            return self._process

        def _build(self) -> None:
            self._method._build()  # pyright: ignore[reportPrivateUsage]

        @staticmethod
        def execute_R_process(
            args: list[str | bytes | PathLike[str] | PathLike[bytes]],
            parameter_read_fd: int | None,
            data: bytes | None,
        ) -> tuple[subprocess.CompletedProcess[bytes], bytes]:
            """
            Run the process specified by `args`, which is passed into `subprocess.run`
            as the first argument.
            This method adds the `METHOD_ARG_READ_FD` environment variable whose value is `str(parameter_read_fd)`.
            This method blocks thread execution until the process completes.

            :param list[str|bytes|PathLike[str]|PathLike[bytes]] args: The argument list to pass to `subprocess.run`.
            :param int parameter_read_fd: A file descriptor number from which R will read method parameters.
            :param bytes | None data: Data that is written to the executed process's STDIN.
            :return subprocess.CompletedProcess[bytes]: The completed process.
            """
            # We must pass the parent process ENV so we don't need to explicitly
            # manage the envvars for R and Rscript to work correctly.
            # We also need to pass `METHOD_ARG_READ_FD` so the R script can determine
            # the correct pipe FD (`read_fd`) to read from to determine the function
            # parameters for SRCGrob that were written to `write_fd`.
            image_data_fd = memfd_create("image_data", 0)
            pass_fds = [image_data_fd]

            try:
                subprocess_env = merge(
                    os.environ.copy(), {"IMAGE_DATA_FD": str(image_data_fd)}
                )

                if parameter_read_fd is not None:
                    # pass the read end of the pipe,
                    # so the process can read whatever we write to write_fd
                    pass_fds.append(parameter_read_fd)
                    subprocess_env["METHOD_ARG_READ_FD"] = str(parameter_read_fd)

                proc = subprocess.run(
                    args,
                    pass_fds=pass_fds,
                    env=cast(Mapping[str, Any], subprocess_env),
                    input=data,
                    text=False,
                    capture_output=True,
                )

                _ = os.lseek(image_data_fd, 0, 0)
                with os.fdopen(image_data_fd, "rb") as f:
                    img_data = f.read()
                return (proc, img_data)
            finally:
                try:
                    os.close(image_data_fd)
                except:
                    pass

        @staticmethod
        def handle_process_errors(
            proc: subprocess.CompletedProcess[bytes], log: Logger | None = None
        ) -> None:
            """
            Decode a finished process's STDERR.
            If the process's STDOUT is empty, an error is considered to have
            occurred, and an exception is raised. Otherwise, STDERR is
            logged and the function returns.

            :param subprocess.CompletedProcess[bytes] proc: The completed process.
            :param Logger log: The Logger that is written to
            :raises Exception: Raised only if STDERR is not empty and STDOUT is empty.
            """
            if proc.returncode == 0:
                return

            stdout_decoded = proc.stdout.decode("utf-8")
            stderr_decoded = proc.stderr.decode("utf-8")

            if not stderr_decoded and stdout_decoded:
                # Log the error because it is likely the application executing
                # Rscript correctly, or something else is wrong with Rscript,
                # but not the executing script itself.
                if log is not None:
                    log.error(
                        "Failure running Rscript.",
                        exc_info=Exception(
                            f"STDOUT: {stdout_decoded}\nSTDERR: {stderr_decoded}"
                        ),
                    )
                raise RscriptProcessError(proc)

            raise RscriptScriptError(proc)

        def execute(
            self,
        ) -> tuple[subprocess.CompletedProcess[bytes], bytes]:
            """
            Execute the configured R script.

            :return CompletedProcess[bytes]: The completed process object from `process.run(...)`
            """
            This = RProcessStepBuilder.RProcessExecutorStepBuilder

            try:
                self._build()

                if self._log is not None:
                    self._log.debug(
                        f"Running `{self.process._rscript_path} {self.script._rscript}`"  # pyright: ignore[reportPrivateUsage]
                    )

                if self.process._rscript_path is None or self.script._rscript is None:  # pyright: ignore[reportPrivateUsage]
                    raise Exception(
                        "An unexpected error occurred with the executor state. This should have been caught when the builder was built."
                    )

                (proc, img_data) = This.execute_R_process(
                    [self.process._rscript_path, self.script._rscript]  # pyright: ignore[reportPrivateUsage]
                    + self.script._args,  # pyright: ignore[reportPrivateUsage]
                    self.method._read_fd,  # pyright: ignore[reportPrivateUsage]
                    self.method._data,  # pyright: ignore[reportPrivateUsage]
                )
            finally:
                if self.method._read_fd:  # pyright: ignore[reportPrivateUsage]
                    os.close(self.method._read_fd)  # pyright: ignore[reportPrivateUsage]

            This.handle_process_errors(proc, self._log)

            return (proc, img_data)
