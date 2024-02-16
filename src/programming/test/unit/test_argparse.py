from argparse import ArgumentError, ArgumentParser, ArgumentTypeError, Namespace

import pytest
from BL_Python.programming.cli.argparse import (
    DisallowDuplicateValues,
    associate_disallow_duplicate_values,
    disallow,
)

# pyright: reportUnknownVariableType=false
# pyright: reportUninitializedInstanceVariable=false


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
        a: str

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
        a: str

    parser = ArgumentParser()
    argument_action = DisallowDuplicateValues(["-a"], "a")
    namespace = ParserNamespace()

    _ = argument_action.__call__(parser, namespace, "value", "-a")
    with pytest.raises(
        ArgumentError,
        match=r"argument -a: The \['-a'] argument does not allow duplicate values\. The value `value` duplicates the value `value`\.",
    ):
        # the Action is called once for every specification of the argument
        # this would be the equivalent of a command like `cmd -a value -a value`
        _ = argument_action.__call__(parser, namespace, "value", "-a")


def test__associate_disallow_duplicate_values__allows_use_of_associated_arguments_with_differing_values():
    class ParserNamespace(Namespace):
        a: str
        b: str

    parser = ArgumentParser()
    # associate "b" with "a" - this means "b" cannot have
    # the same value as "a" but the reverse is not true.
    action = associate_disallow_duplicate_values("a")
    argument_action = action(["-b"], "b")
    namespace = ParserNamespace(a="value")

    # only call for the argument that is associated with another
    _ = argument_action.__call__(parser, namespace, "other_value", "-b")
    assert isinstance(namespace.b, list)
    assert "value" in namespace.a
    assert "other_value" in namespace.b


def test__associate_disallow_duplicate_values__raises_ArgumentError_when_associated_argument_value_is_not_unique():
    class ParserNamespace(Namespace):
        a: str
        b: str

    parser = ArgumentParser()
    action = associate_disallow_duplicate_values("a")
    argument_action = action(["-b"], "b")
    namespace = ParserNamespace(a="value")

    # only call for the argument that is associated with another
    with pytest.raises(
        ArgumentError,
        match=r"argument -b: The \['-b'] argument cannot be equivalent to the `a` argument\. The value `value` is equivalent to the value `value`\.",
    ):
        _ = argument_action.__call__(parser, namespace, "value", "-b")


def test__associate_disallow_duplicate_values__allows_use_of_associated_arguments_when_associated_argument_is_repeated():
    class ParserNamespace(Namespace):
        a: list[str]
        b: str

    parser = ArgumentParser()
    action = associate_disallow_duplicate_values("a")
    argument_action = action(["-b"], "b")
    # when an argument is repated for a command it is stored as a list
    namespace = ParserNamespace(a=["value", "other_value"])

    _ = argument_action.__call__(parser, namespace, "another_value", "-b")
    assert isinstance(namespace.b, list)
    assert "value" in namespace.a
    assert "other_value" in namespace.a
    assert "another_value" in namespace.b


def test__associate_disallow_duplicate_values__raises_ArgumentError_when_handling_non_unique_values_when_associated_argument_is_repeated():
    class ParserNamespace(Namespace):
        a: list[str]
        b: str

    parser = ArgumentParser()
    action = associate_disallow_duplicate_values("a")
    argument_action = action(["-b"], "b")
    # when an argument is repated for a command it is stored as a list
    namespace = ParserNamespace(a=["value", "other_value"])

    with pytest.raises(
        ArgumentError,
        match=r"argument -b: The \['-b'] argument cannot be equivalent to the `a` argument\. The value `value` is equivalent to the value `\['value', 'other_value']`\.",
    ):
        _ = argument_action.__call__(parser, namespace, "value", "-b")


def test__associate_disallow_duplicate_values__falls_back_to_DisallowDuplicateValues_when_associated_argument_value_is_unique():
    class ParserNamespace(Namespace):
        a: str
        b: str

    parser = ArgumentParser()
    action = associate_disallow_duplicate_values("a")
    argument_action = action(["-b"], "b")
    namespace = ParserNamespace(a="value")

    _ = argument_action.__call__(parser, namespace, "other_value", "-b")
    # `associate_disallow_duplicate_values` will always fall back,
    # we just explicitly test for the behavior here.
    with pytest.raises(
        ArgumentError,
        match=r"argument -b: The \['-b'] argument does not allow duplicate values\. The value `other_value` duplicates the value `other_value`\.",
    ):
        _ = argument_action.__call__(parser, namespace, "other_value", "-b")
