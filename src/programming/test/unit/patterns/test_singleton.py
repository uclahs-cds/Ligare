from typing import Any

import pytest
from BL_Python.programming.patterns.singleton import Singleton


def test__multiple_instantiation_returns_same_instance():
    class Foo(metaclass=Singleton):
        ...

    assert Foo() == Foo()


def test__prevents_attribute_changes():
    class Foo(metaclass=Singleton):
        x: int = 123

    foo = Foo()
    foo.x = 456

    assert foo.x == 123
    assert Foo.x == 123


@pytest.mark.parametrize("block_value", [None, True, 1, 0, [], {}, "1", "0", " ", ""])
def test__prevents_attribute_changes_when_configured_with_blocking_values(
    block_value: Any,
):
    class Foo(metaclass=Singleton):
        _block_change = block_value
        x: int = 123

    foo = Foo()
    foo.x = 456

    assert foo.x == 123
    assert Foo.x == 123


@pytest.mark.parametrize("block_value", [None, True, 1, 0, [], {}, "1", "0", " ", ""])
def test__prevents_attribute_deletion_when_configured_with_blocking_values(
    block_value: Any,
):
    class Foo(metaclass=Singleton):
        _block_change = block_value
        x: int = 123

    foo = Foo()

    del foo.x

    assert foo.x == 123
    assert Foo.x == 123


def test__allows_attribute_changes_when_configured_with_non_blocking_value():
    class Foo(metaclass=Singleton):
        _block_change = False
        x: int = 123

    foo1 = Foo()
    foo1.x = 456
    foo2 = Foo()

    assert foo1.x == 456
    assert foo2.x == 456
    assert Foo.x == 123


def test__allows_attribute_deletion_when_configured_with_non_blocking_value():
    class Foo(metaclass=Singleton):
        _block_change = False
        x: int = 123

    foo = Foo()

    # this should fail because the attribute
    # is on the class, not the instance
    with pytest.raises(AttributeError):
        del foo.x

    setattr(foo, "y", "456")
    # this should succeed because the attribute
    # is on the instance, not the class
    delattr(foo, "y")

    assert hasattr(foo, "x")
    assert hasattr(Foo, "x")
    assert not hasattr(foo, "y")
    assert not hasattr(Foo, "y")
