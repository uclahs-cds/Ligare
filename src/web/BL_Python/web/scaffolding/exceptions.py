from typing_extensions import override


class OutputDirectoryException(Exception):
    _msg: str
    _directory: str

    def __init__(self, msg: str, directory: str) -> None:
        super().__init__()
        self._msg = msg
        self._directory = directory

    @override
    def __str__(self):
        return f"Invalid working directory `{self._directory}`.\n{self._msg}"
