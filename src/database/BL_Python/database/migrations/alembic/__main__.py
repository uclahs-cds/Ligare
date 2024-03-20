import logging
import sys
import tempfile
from os import environ
from pathlib import Path

# this is Alembic's main entry point
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

    # if a config file has been specified on the
    # command line, use it and don't create
    # a temporary one
    # print(alembic_parsed_args)
    args = set(argv)

    if (
        not args
        or "-c" in args
        or "--config" in args
        or "-h" in args
        or "--help" in args
    ):
        logger.debug("Running unmodified `alembic` command.")
        # run Alembic
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

        argv = ["-c", f2.name] + argv

        # run Alembic
        return alembic_main(argv)


if __name__ == "__main__":
    bl_alembic()
