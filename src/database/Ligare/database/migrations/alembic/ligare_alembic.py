import logging
import sys
from logging import Logger
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Callable, cast

import alembic.util.messaging

# this is Alembic's main entry point
from alembic.config import CommandLine, Config
from alembic.config import main as alembic_main
from attr import dataclass
from typing_extensions import final


@final
class LigareAlembic:
    DEFAULT_CONFIG_NAME: str = "alembic.ini"
    LOG_LEVEL_NAME: str = "LOG_LEVEL"

    _run: Callable[[], None]
    _log: Logger

    @dataclass
    class FileCopy:
        source: Path
        destination: Path

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
            self._run = lambda: self._run_with_config(argv)

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

    def _run_with_config(self, argv: list[str]) -> None:
        """
        Calls `alembic` programmatically either:
            - if the file 'alembic.ini' exists in the same working
                directory in which the command is run.
            - if the file 'alembic.ini' does not exist and after creating
                a temporary configuration file from the Ligare default Alembic
                config, and forcing the temporary configuration file to be used
                by `alembic`.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return None:
        """
        self._log.debug("Running `alembic` with modified command.")
        self._write_ligare_alembic_config()
        argv = ["-c", LigareAlembic.DEFAULT_CONFIG_NAME] + argv

        self._execute_alembic(argv)

    def _execute_alembic(self, argv: list[str]) -> None:
        """
        Programmatically run `alembic`.

        :param list[str] argv: The command line arguments to be parsed by ArgumentParser.
        :return None:
        """
        config = self._get_config(argv)

        with self._initialize_alembic(config) as msg_capture:
            self._log.info("Starting execution.")
            try:
                return alembic_main(argv)
            except SystemExit as e:
                # If SystemExit is from anything other than
                # needing to create the init dir, then crash.
                # This is doable/reliable because Alembic first writes
                # a message that the directory needs to be created,
                # then calls `sys.exit(-1)`.
                if not msg_capture.seen:
                    self._log.error("Unexpected error from Alembic.", exc_info=e)
                    raise

                self._log.debug(
                    f"The Alembic initialization error was seen. Ignoring `{SystemExit.__name__}` exception."
                )

        self._log.info("Finished execution.")

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
        ligare_alembic_file_dir = Path(__file__).resolve().parent

        files = [
            LigareAlembic.FileCopy(
                Path(ligare_alembic_file_dir, f"_replacement_{basename}.py"),
                Path(Path.cwd(), Path(script_location, f"{basename}.py")),
            )
            for basename in ["env", "env_setup"]
        ]

        self._log.debug(f"Rewriting base Alembic files: '{files}'")
        # force the overwrite because Alembic creates the
        # files that we want to replace.
        self._copy_files(files, force_overwrite=True)

    def _write_ligare_alembic_config(
        self,
    ) -> None:
        """
        Write the Ligare Alembic tool's default configuration file to a temp file.

        :yield Generator[tempfile._TemporaryFileWrapper[bytes], Any, None]: The temp file.
        """
        config_file_destination = Path(Path.cwd(), LigareAlembic.DEFAULT_CONFIG_NAME)
        if config_file_destination.exists():
            self._log.debug(
                f"Configuration file '{LigareAlembic.DEFAULT_CONFIG_NAME}' exists. Will not attempt to create it."
            )
            return

        # copy the default alembic.ini
        # to the directory in which ligare-alembic is executed.
        self._log.debug(
            f"Writing configuration file '{LigareAlembic.DEFAULT_CONFIG_NAME}'."
        )
        self._copy_files([
            LigareAlembic.FileCopy(
                Path(
                    Path(__file__).resolve().parent, LigareAlembic.DEFAULT_CONFIG_NAME
                ),
                config_file_destination,
            )
        ])

    def _copy_files(self, files: list[FileCopy], force_overwrite: bool = False):
        for file in files:
            write_mode = "w+b" if force_overwrite else "x+b"
            try:
                with (
                    open(file.source, "r") as source,
                    open(file.destination, write_mode) as destination,
                ):
                    destination.writelines(cast(BinaryIO, source.buffer))
            except FileExistsError as e:
                if e.filename != str(file.destination):
                    raise

                self._log.debug(
                    f"The file '{file.destination}' already exists. Refusing to overwrite, but ignoring exception."
                )

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
                logging.getLogger("alembic.util.messaging").disabled = True

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
                logging.getLogger("alembic.util.messaging").disabled = False
                self._log.debug(f"Exiting `{MsgCaptureCtxManager.__name__}` context.")
                alembic.util.messaging.msg = _msg_original

                if exc_type is not None:
                    return False

                return True

        return MsgCaptureCtxManager(self._log)

    def run(self) -> None:
        """
        Run Alembic migrations, initializing Alembic if necessary.

        :return None:
        """
        self._log.debug("Bootstrapping and executing `alembic` process.")

        return self._run()
