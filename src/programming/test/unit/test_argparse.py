from argparse import ArgumentError, ArgumentParser, ArgumentTypeError, Namespace

import pytest
from BL_Python.programming.cli.argparse import DisallowDuplicateValues, disallow


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


def test__DisallowDuplicateValues__allows_repeated_use_of_argument():
    class ParserNamespace(Namespace):
        a: str  # pyright: ignore[reportUninitializedInstanceVariable]

    parser = ArgumentParser()
    argument_action = DisallowDuplicateValues(["-a"], "a")
    namespace = ParserNamespace()

    # the Action is called once for every specification of the argument
    # this would be the equivalent of a command like `cmd -a value -a other_value`
    _ = argument_action.__call__(parser, namespace, "value", "-a")
    _ = argument_action.__call__(parser, namespace, "other_value", "-a")
    assert isinstance(namespace.a, list)
    assert "value" in namespace.a
    assert "other_value" in namespace.a


def test__DisallowDuplicateValues__raises_ArgumentError_when_duplicate_value_for_argument_is_used():
    class ParserNamespace(Namespace):
        a: str  # pyright: ignore[reportUninitializedInstanceVariable]

    parser = ArgumentParser()
    argument_action = DisallowDuplicateValues(["-a"], "a")
    namespace = ParserNamespace()

    with pytest.raises(ArgumentError):
        # the Action is called once for every specification of the argument
        # this would be the equivalent of a command like `cmd -a value -a value`
        _ = argument_action.__call__(parser, namespace, "value", "-a")
        _ = argument_action.__call__(parser, namespace, "value", "-a")
