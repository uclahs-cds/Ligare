import logging
from os import environ

# this is Alembic's main entry point
from .ligare_alembic import LigareAlembic


def ligare_alembic(
    argv: list[str] | None = None,
    log_level: int | str | None = None,
    allow_overwrite: bool | None = None,
) -> None:
    """
    A method to support the `ligare-alembic` command, which replaces `alembic`.

    :param list[str] | None argv: CLI arguments, defaults to None
    :param int | str | None log_level: An integer log level to configure logging verbosity, defaults to None
    """
    logging.basicConfig(level=logging.INFO)
    if not log_level:
        log_level = environ.get(LigareAlembic.LOG_LEVEL_NAME)
        log_level = int(log_level) if log_level else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    LigareAlembic(argv, logger).run()


if __name__ == "__main__":
    ligare_alembic()
