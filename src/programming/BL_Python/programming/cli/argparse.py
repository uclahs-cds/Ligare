from argparse import ArgumentTypeError, FileType
from typing import Callable, TypeVar

_T = TypeVar("_T")

"""

Args:
    values (list[str]): _description_
    argument_name (str): _description_
    type (Callable[[str], _T] | FileType | None, optional): _description_. Defaults to None.
"""


def disallow(
    values: list[str],
    argument_name: str,
    type: Callable[[str], _T] | FileType | None = None,
):
    """
    Disallow a set of `values` for the argument `argument_name`.
    If the value given for `argument_name` is in the list `values`, an `ArgumentTypeError` is raised.

    `disallow` acts as a "pass-through" for setting the `type` of a parameter. It operates by first checking
    whether the value given is disallowed, and then uses `type` to return the new object as if that same `type`
    had been given directly to argparse without using `disallow`.

    If `type` is not specified, `value` is returned as a string.

    :param list[str] values: A list of values that are _not_ allowed for this argument
    :param str argument_name: The name of the argument this applies to
    :param Callable[[str], _T] | FileType | None type: The type of the argument to be created, defaults to None
    """

    def check_disallow(value: str):
        if value in values:
            raise ArgumentTypeError(
                f"`{value}` is not an allowed value of the `{argument_name}` argument."
            )
        return str(value) if type is None else type(value)

    return check_disallow
