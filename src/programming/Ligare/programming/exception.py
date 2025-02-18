"""
Exceptions used by the :ref:`Ligare.web` framework.
"""


class InvalidBuilderStateError(Exception):
    """The builder's state is invalid and the builder cannot execute `build()`."""


class BuilderBuildError(Exception):
    """The builder failed during execution of `build()`."""
