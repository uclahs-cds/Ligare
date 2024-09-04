class InvalidConfigNameError(Exception):
    """The class name used as a configuration type is invalid. The name must end with `Config`."""


class ConfigBuilderStateError(Exception):
    """The config builder has not been configured correctly."""
