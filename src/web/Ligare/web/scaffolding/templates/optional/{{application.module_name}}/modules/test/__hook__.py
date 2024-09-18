from logging import Logger
from typing import Any


def on_create(config: dict[str, Any], log: Logger):
    log.debug(f"Test module hook executed")

    config["module"]["test"] = {}
