from subprocess import CompletedProcess


class RscriptProcessError(Exception):
    """
    An error occurred with `Rscript`.
    Note: This exception is not used when a script executed by `Rscript` errors;
    it is only used when `Rscript` itself raises an error.
    """

    def __init__(self, proc: CompletedProcess[bytes], *args: object) -> None:
        self.proc = proc
        super().__init__(proc.stdout.decode("utf-8"), *args)


class RscriptScriptError(Exception):
    """
    An error occurred executing a script with `Rscript`.
    Note: This exception is not used when `Rscript` itself errors;
    it is only used when a script executed by `Rscript` raises an error.
    """

    def __init__(self, proc: CompletedProcess[bytes], *args: object) -> None:
        self.proc = proc
        super().__init__(proc.stderr.decode("utf-8"), *args)
