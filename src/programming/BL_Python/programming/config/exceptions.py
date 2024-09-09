class InvalidConfigNameError(Exception):
    """The class name used as a configuration type is invalid."""


class NotEndsWithConfigError(InvalidConfigNameError):
    """The name must end with `Config`."""


class ConfigBuilderStateError(Exception):
    """The config builder has not been configured correctly."""
