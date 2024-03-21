import logging
import sys
import tempfile
from contextlib import contextmanager
from logging import Logger
from os import environ
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Generator

import alembic.util.messaging

# this is Alembic's main entry point
from alembic.config import CommandLine, Config
from alembic.config import main as alembic_main
from attr import dataclass
from typing_extensions import final


@final
class BLAlembic:
    _run: Callable[[], None]
    _log: Logger

    def __init__(self, argv: list[str] | None, logger: Logger) -> None:
        """
        _summary_

        :param list[str] | None argv: The command line arguments to be parsed by ArgumentParser.
            If None, this will use `sys.argv[1:]` to use CLI arguments.
        :param Logger logger: A logger for writing messages.
        """
        self._log = logger

        if not argv:
            argv = sys.argv[1:]

        args = set(argv)

        if not args or "-h" in args or "--help" in args:
            self._log.debug(f"Empty or 'help' args passed from Alembic: {args}")
            self._run = lambda: self._run_with_alembic_defaults(argv)
        elif "-c" in args or "--config" in args:
            self._log.debug(f"'config' args passed from Alembic: {args}")
            self._run = lambda: self._run_with_specified_config(argv)
        else:
            self._log.debug(f"Execution-only args passed from Alembic: {args}")
            self._run = lambda: self._run_with_bl_alembic_config(argv)

    def _get_config(self, argv: list[str]) -> Config:
        """
        Get a parsed Alembic INI file as a `Config` object.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return Config: The `Config` object with options set from an INI file.
        """
        # needs to open the config and return it
        # so we can get the alembic migration directory
        alembic_cli = CommandLine()
        parsed_args = alembic_cli.parser.parse_args(argv)
        self._log.debug(f"Parsed arguments: {parsed_args}")
        config = Config(parsed_args.config)
        self._log.debug(f"Instantiated config: {repr(config)}")
        return config

    def _run_with_alembic_defaults(self, argv: list[str]) -> None:
        """
        Calls `alembic` programmatically.

        Used when no command line arguments, or `-h` or `--help`, are specified.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return None:
        """
        self._log.debug("Running unmodified `alembic` command.")
        return alembic_main(argv)

    def _run_with_specified_config(self, argv: list[str]) -> None:
        """
        Calls `alembic` programmatically.

        Used when `-c` or `--config` are specified.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return None:
        """
        self._log.debug("Running unmodified `alembic` command.")
        self._execute_alembic(argv)

    def _run_with_bl_alembic_config(self, argv: list[str]) -> None:
        """
        Calls `alembic` programmatically after creating a temporary
        config file from the BL_Python default Alembic config, and
        forcing the temporary config file to be used by `alembic`.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return None:
        """
        self._log.debug("Running `alembic` with modified command.")
        with self._write_bl_alembic_config() as config_file:
            argv = ["-c", config_file.name] + argv

            self._execute_alembic(argv)

    def _execute_alembic(self, argv: list[str]) -> None:
        """
        Programmatically run `alembic`.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return None:
        """
        config = self._get_config(argv)

        with self._initialize_alembic(config) as msg_capture:
            try:
                return alembic_main(argv)
            except SystemExit as e:
                self._log.error(e)
                # If SystemExit is from anything other than
                # needing to create the init dir, then crash.
                # This is doable/reliable because Alembic first writes
                # a message that the directory needs to be created,
                # then calls `sys.exit(-1)`.
                if not msg_capture.seen:
                    raise

                self._log.debug(
                    f"The Alembic initialization error was seen. Ignoring `{SystemExit.__name__}` exception."
                )

    def _initialize_alembic(self, config: Config):
        """
        Set up Alembic to run `alembic init` programmatically if it is needed.

        :param Config config: The config, parsed from an Alembic INI configuration file.
        :return MsgCaptureCtxManager: A type indicating whether an expected message was
            written by Alembic. In the case of this method, if the "use the 'init'"
            message is seen, then `alembic init` is executed. This type can be used to
            determine whether `alembic init` was executed.
        :return MsgCaptureCtxManager:
        """
        script_location = config.get_main_option("script_location") or "alembic"

        def _msg_new(msg: Callable[[str, bool, bool, bool], None]):
            nonlocal script_location
            self._log.debug("Executing `alembic init`.")
            msg(
                "'alembic' migration directory does not exist. Creating it.",
                # these bool values are defaults for Alembic msg function
                True,
                False,
                False,
            )
            alembic_main(["init", script_location])

            self._overwrite_alembic_env_files(config)

        return self._alembic_msg_capture(
            "use the 'init' command to create a new scripts folder", _msg_new
        )

    def _overwrite_alembic_env_files(self, config: Config) -> None:
        """
        Overwrite env.py and env_setup.py in an Alembic migrations directory.
        Currently this only runs if `alembic init` is executed, and care must
        be taken if we intend to change this to overwrite the files if they exist.
        The files will exist if `alembic init` was executed prior to this tool.

        :param Config config: The config, parsed from an Alembic INI configuration file.
        :return None:
        """
        script_location = config.get_main_option("script_location") or "alembic"
        bl_python_alembic_file_dir = Path(__file__).resolve().parent

        files = [
            (
                Path(bl_python_alembic_file_dir, f"_replacement_{basename}.py"),
                Path(script_location, f"{basename}.py"),
            )
            for basename in ["env", "env_setup"]
        ]

        for file in files:
            self._log.debug(f"Rewriting base Alembic files: {file}")
            with (
                open(file[0], "r") as replacement,
                open(file[1], "w+b") as original,
            ):
                original.writelines(replacement.buffer)

    @contextmanager
    def _write_bl_alembic_config(
        self,
    ) -> "Generator[tempfile._TemporaryFileWrapper[bytes], Any, None]":  # pyright: ignore[reportPrivateUsage]
        """
        Write the BL_Python Alembic tool's default configuration file to a temp file.

        :yield Generator[tempfile._TemporaryFileWrapper[bytes], Any, None]: The temp file.
        """
        with tempfile.NamedTemporaryFile("w+b") as temp_config_file:
            self._log.debug(f"Temp file created at '{temp_config_file.name}'.")
            with open(
                Path(Path(__file__).resolve().parent, "alembic.ini"), "r"
            ) as default_config_file:
                self._log.debug(
                    f"Writing config file 'alembic.ini' to temp file '{temp_config_file.name}'."
                )
                temp_config_file.writelines(default_config_file.buffer)

            # the file will not be read correctly
            # without seeking to the 0th byte
            _ = temp_config_file.seek(0)

            # yield so the temp file isn't deleted
            yield temp_config_file

    def _alembic_msg_capture(
        self,
        msg_to_capture: str,
        callback: Callable[[Callable[[str, bool, bool, bool], None]], None],
    ):
        """
        Capture a specific message written by Alembic, and call `callback` if it matches.

        This method override's Alembic's `msg` function and restores it when the
        context is closed.

        :param str msg_to_capture: The specific message to monitor in Alembic's writes.
        :param Callable[[Callable[[str, bool, bool, bool], None]], None] callback:
            A callable that receives Alembic's `msg` function as a parameter.
        :return MsgCaptureCtxManager:
        """

        OVERRIDDEN_ORIGINAL_ATTR_NAME = "_overridden_original"
        if hasattr(alembic.util.messaging.msg, OVERRIDDEN_ORIGINAL_ATTR_NAME):
            # if the attr exists that means we have already overriden it,
            # so we set `_msg_original` to the real original.
            self._log.debug(
                f"`alembic.util.messaging.msg` has already been overwritten. Using `{OVERRIDDEN_ORIGINAL_ATTR_NAME}` attribute to get the original method."
            )
            _msg_original = getattr(
                alembic.util.messaging.msg, OVERRIDDEN_ORIGINAL_ATTR_NAME
            )
        else:
            self._log.debug(
                f"`alembic.util.messaging.msg` has not been overridden. Using it as the original method."
            )
            # if the attr does not exist, then we assume `msg` is
            # the original Alembic `msg` function.
            _msg_original: Callable[[str, bool, bool, bool], None] = (
                alembic.util.messaging.msg
            )

        @dataclass
        class MessageSeen:
            seen: bool = False

        @final
        class MsgCaptureCtxManager:
            _msg_seen: MessageSeen = MessageSeen()
            _log: Logger

            def __init__(self, logger: Logger) -> None:
                self._log = logger

            def __enter__(self) -> MessageSeen:
                """
                Replace Alembic's `msg` function in order to execute
                a callback when certain messages are seen.

                :return _type_: _description_
                """
                self._log.debug(f"Entering `{MsgCaptureCtxManager.__name__}` context.")

                def _msg_new(
                    msg: str,
                    newline: bool = True,
                    flush: bool = False,
                    quiet: bool = False,
                ):
                    if msg_to_capture in msg:
                        self._log.debug(
                            f"The msg '{msg_to_capture}' was written by Alembic."
                        )
                        callback(_msg_original)
                        self._msg_seen.seen = True
                    else:
                        _msg_original(msg, newline, flush, quiet)

                setattr(
                    _msg_new, OVERRIDDEN_ORIGINAL_ATTR_NAME, alembic.util.messaging.msg
                )

                self._log.debug(
                    f"Overwritting `alembic.util.messaging.msg` with `{repr(_msg_new)}`."
                )
                alembic.util.messaging.msg = _msg_new

                return self._msg_seen

            def __exit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: TracebackType | None,
            ) -> bool:
                """
                Revert replacing Alembic's `msg` function by restoring the original.

                :param type[BaseException] | None exc_type:
                :param BaseException | None exc_val:
                :param TracebackType | None exc_tb:
                :return bool:
                """
                self._log.debug(f"Exiting `{MsgCaptureCtxManager.__name__}` context.")
                alembic.util.messaging.msg = _msg_original
                return True

        return MsgCaptureCtxManager(self._log)

    def run(self) -> None:
        """
        Run Alembic migrations, initializing Alembic if necessary.

        :return None:
        """
        self._log.debug("Bootstrapping and executing `alembic` process.")
        return self._run()


def bl_alembic(
    argv: list[str] | None = None, log_level: int | str | None = None
) -> None:
    """
    A method to support the `bl-alembic` command, which replaces `alembic.

    :param list[str] | None argv: CLI arguments, defaults to None
    :param int | str | None log_level: An integer log level to configure logging verbosity, defaults to None
    """
    logging.basicConfig(level=logging.INFO)
    if not log_level:
        log_level = environ.get("LOG_LEVEL")
        log_level = int(log_level) if log_level else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    bla = BLAlembic(argv, logger)
    bla.run()


if __name__ == "__main__":
    bl_alembic()
