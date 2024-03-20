import logging
import sys
import tempfile
from os import environ
from pathlib import Path

import alembic.util.messaging

# this is Alembic's main entry point
from alembic.config import CommandLine, Config
from alembic.config import main as alembic_main


def bl_alembic(argv: list[str] | None = None, log_level: int | str | None = None):
    logging.basicConfig(level=logging.INFO)
    if not log_level:
        log_level = environ.get("LOG_LEVEL")
        log_level = int(log_level) if log_level else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    if not argv:
        argv = sys.argv[1:]

    args = set(argv)

    if not args or "-h" in args or "--help" in args:
        logger.debug("Running unmodified `alembic` command.")
        # run Alembic
        return alembic_main(argv)

    # needs to open the config and return it
    # so we can get the alembic migration directory
    def get_config_obj(argv):
        alembic_cli = CommandLine()
        parsed_args = alembic_cli.parser.parse_args(argv)
        return Config(parsed_args.config)

    # if a config file has been specified on the
    # command line, use it and don't create
    # a temporary one
    if "-c" in args or "--config" in args:
        logger.debug("Running unmodified `alembic` command.")
        conf = get_config_obj(argv)
        print(conf.get_main_option("script_location"))
        return alembic_main(argv)

    logger.debug("Running `alembic` with modified command.")
    with (
        open(Path(Path(__file__).resolve().parent, "alembic.ini"), "r") as f1,
        tempfile.NamedTemporaryFile("w+b") as f2,
    ):
        f2.writelines(f1.buffer)
        # the file will not be read correctly
        # without seeking to the 0th byte
        _ = f2.seek(0)

        conf = Config(f2.name)

        argv = ["-c", f2.name] + argv
        conf = get_config_obj(argv)
        script_location = conf.get_main_option("script_location") or "alembic"

        _created_alembic_dir_marker = False
        _msg_original = alembic.util.messaging.msg

        def _msg_new(
            msg: str, newline: bool = True, flush: bool = False, quiet: bool = False
        ):
            nonlocal _created_alembic_dir_marker
            nonlocal script_location
            if "use the 'init' command to create a new scripts folder" in msg:
                _msg_original(
                    "'alembic' migration directory does not exist. Creating it."
                )
                alembic_main(["init", script_location])
                _created_alembic_dir_marker = True
            else:
                _msg_original(msg, newline, flush, quiet)

        alembic.util.messaging.msg = _msg_new
        # run Alembic
        try:
            return alembic_main(argv)
        except SystemExit:
            if not _created_alembic_dir_marker:
                raise
        finally:
            alembic.util.messaging.msg = _msg_original


if __name__ == "__main__":
    bl_alembic()
