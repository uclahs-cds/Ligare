from argparse import (
    Action,
    ArgumentError,
    ArgumentParser,
    ArgumentTypeError,
    FileType,
    Namespace,
)
from typing import Any, Callable, Iterable, Sequence, TypeVar

from typing_extensions import override

_T = TypeVar("_T")


class DisallowDuplicateValues(Action):
    """
    Checks for duplicated values for the argument using this Action.
    If a value is duplicated, an ArgumentError is raised. Otherwise,
    the argument is treated as a "Append" action, and the value is
    added to a list of values for that argument.

    :param DisallowDuplicateValues Action: self
    :raises ArgumentError: Raised when a value for the argument is duplicated
    """

    @override
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        attr: list[Any] | None
        if not (attr := getattr(namespace, self.dest, None)):
            # using a list assumes this should do an "append" operation,
            # which makes sense for "duplicate" values.
            attr = []
            setattr(namespace, self.dest, attr)

        if values in attr:
            duplicate_value = [value for value in attr if value == values][0]
            raise ArgumentError(
                self,
                # This assumes str(values) makes sense, but it's possible it won't.
                # Also, while at first glance that statement "The value `foo` duplicates the value `foo`"
                # doesn't seem helpful, it is possible that an argument's type is something that normalizes
                # argument values. For example, this message might say "The value `foo-bar` duplicates the value `foo_bar`."
                f"The {self.option_strings} argument does not allow duplicate values. The value `{values}` duplicates the value `{duplicate_value}`.",
            )

        attr.append(values)
        setattr(namespace, self.dest, attr)


def associate_disallow_duplicate_values(associated_arg: str):
    """
    Associate an argument with another, preventing the two from sharing the same value.
    If the values are not equivalent, the action then falls back to `DisallowDuplicateValues`.

    :param str associated_arg: The argument with which to associate the argument that this Action is applied to.
    :raises ArgumentError: Raised if the value of the argument using this Action is equivalent to the argument it is associated with.
    :return AssociatedDisallowDuplicateValues:
    """

    class AssociatedDisallowDuplicateValues(Action):
        # fmt: off
        def __init__(
            self, option_strings: Sequence[str], dest: str, nargs: int | str | None = None, const: _T | None = None,
            default: _T | str | None = None, type: Callable[[str], _T] | FileType | None = None,
            choices: Iterable[_T] | None = None, required: bool = False, help: str | None = None,
            metavar: str | tuple[str, ...] | None = None,
        ) -> None:
            super().__init__(option_strings, dest, nargs, const, default, type, choices, required, help, metavar)

            self._disallow_duplicate_values = DisallowDuplicateValues(
                option_strings, dest, nargs, const, default, type, choices, required, help, metavar
            )
            # fmt: on

        @override
        def __call__(
            self,
            parser: ArgumentParser,
            namespace: Namespace,
            values: str | Sequence[Any] | None,
            option_string: str | None = None,
        ) -> None:
            if (associated_arg_value := getattr(namespace, associated_arg, None)):
                if associated_arg_value == values or (isinstance(associated_arg_value, Iterable) and values in associated_arg_value):
                    raise ArgumentError(
                        self,
                        f"The {self.option_strings} argument cannot be equivalent to the `{associated_arg}` argument. The value `{values}` is equivalent to the value `{associated_arg_value}`.",
                    )

            # this will set the value as long as the
            # argument value is not duplicated itself
            self._disallow_duplicate_values(parser, namespace, values, option_string)

    return AssociatedDisallowDuplicateValues


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
