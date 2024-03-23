import logging
from os import environ

# this is Alembic's main entry point
from .bl_alembic import BLAlembic


def bl_alembic(
    argv: list[str] | None = None,
    log_level: int | str | None = None,
    allow_overwrite: bool | None = None,
) -> None:
    """
    A method to support the `bl-alembic` command, which replaces `alembic.

    :param list[str] | None argv: CLI arguments, defaults to None
    :param int | str | None log_level: An integer log level to configure logging verbosity, defaults to None
    """
    logging.basicConfig(level=logging.INFO)
    if not log_level:
        log_level = environ.get(BLAlembic.LOG_LEVEL_NAME)
        log_level = int(log_level) if log_level else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    if allow_overwrite is None:
        _allow_overwrite = environ.get(BLAlembic.ALLOW_OVERWRITE_NAME)
        allow_overwrite = (_allow_overwrite.lower() if _allow_overwrite else None) in [
            "true",
            "1",
        ]

    BLAlembic(argv, logger, allow_overwrite).run()


if __name__ == "__main__":
    bl_alembic()
