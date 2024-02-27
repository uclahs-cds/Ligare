from typing import Any

import pytest
from BL_Python.programming.patterns.singleton import Singleton


def test__multiple_instantiation_returns_same_instance():
    class Foo(metaclass=Singleton):
        ...

    assert Foo() == Foo()


def test__prevents_attribute_changes_by_default():
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


def test__allows_attribute_changes_when_configured_with_non_blocking_value_when_block_change_is_false():
    class Foo(metaclass=Singleton):
        _block_change = False
        x: int = 123

    foo1 = Foo()
    foo1.x = 456
    foo2 = Foo()

    assert foo1.x == 456
    assert foo2.x == 456
    assert Foo.x == 123


def test__allows_attribute_deletion_when_configured_with_non_blocking_value_when_block_change_is_false():
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


@pytest.mark.parametrize("block_change", [True, False])
def test__prevents_arbitrary_class_attribute_deletion_on_instances(block_change: bool):
    class Foo(metaclass=Singleton):
        _block_change = block_change
        _arbitrary = True

    foo = Foo()

    # when _block_change is True, deletion is ignored
    if block_change:
        del foo._arbitrary  # pyright: ignore[reportPrivateUsage]
        delattr(foo, "_arbitrary")
    else:
        with pytest.raises(AttributeError):
            del foo._arbitrary  # pyright: ignore[reportPrivateUsage]

        with pytest.raises(AttributeError):
            delattr(foo, "_arbitrary")

    assert hasattr(foo, "_arbitrary")
    assert hasattr(Foo, "_arbitrary")


@pytest.mark.parametrize("block_change", [True, False])
def test__allows_arbitrary_class_attribute_deletion_on_classes(block_change: bool):
    class Foo(metaclass=Singleton):
        _block_change = block_change
        _arbitrary = True

    foo = Foo()

    # This cannot be intercepted, even
    # by the `__delete__` descriptor.
    # As such, it is always allowed.
    del Foo._arbitrary  # pyright: ignore[reportPrivateUsage]

    assert not hasattr(foo, "_arbitrary")
    assert not hasattr(Foo, "_arbitrary")
