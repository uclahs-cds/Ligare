from logging import Logger
from typing import Any


def on_create(config: dict[str, Any], log: Logger):
    """Called when an application is created."""

    config["module"]["database"] = {}

    connection_string = input(
        "\nEnter a database connection string.\nBy default this is `sqlite:///:memory:?check_same_thread=False`.\nRetain this default by pressing enter, or type something else.\n> "
    )

    config["module"]["database"]["connection_string"] = (
        connection_string
        if connection_string
        else "sqlite:///:memory:?check_same_thread=False"
    )
    log.info(
        f"Using database connection string `{config['module']['database']['connection_string']}`"
    )
