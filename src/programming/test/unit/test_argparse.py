from argparse import ArgumentTypeError

import pytest
from BL_Python.programming.cli.argparse import disallow


def test__disallow__raises_ArgumentTypeError_when_disallowed_value_is_used():
    argument_type = disallow(["foo"], "argument")

    with pytest.raises(ArgumentTypeError):
        _ = argument_type("foo")


def test__disallow__returns_argument_value_when_disallowed_value_is_not_used():
    argument_type = disallow(["foo"], "argument")

    value = argument_type("bar")

    assert "bar" == value


def test__disallow__returns_argument_value_as_custom_type_when_disallowed_value_is_not_used():
    # rather than defining a callable type, we can just use a lambda
    argument_type = disallow(["foo"], "argument", lambda value: int(value) + 1)

    value = argument_type("1")

    assert 2 == value
