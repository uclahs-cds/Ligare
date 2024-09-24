# pyright: reportPrivateUsage=false

from typing import Any

import pytest
from Ligare.programming.patterns.singleton import Singleton


def test__multiple_instantiation_returns_same_instance():
    class Foo(metaclass=Singleton): ...

    assert Foo() == Foo()


@pytest.mark.parametrize("block_change", [True, False, None])
def test__multiple_instantiation_returns_same_instance_when_block_change_declared(
    block_change: bool | None,
):
    class Foo(metaclass=Singleton):
        _block_change = block_change

    assert Foo() == Foo()


def test__prevents_attribute_changes_by_default():
    class Foo(metaclass=Singleton):
        x: int = 123

    foo = Foo()
    foo.x = 456

    assert foo.x == 123
    assert Foo.x == 123


def test__prevents_block_change_alteration_when_block_change_is_true():
    class Foo(metaclass=Singleton):
        _block_change = True
        x: int = 123

    setattr(Foo, "_block_change", False)
    foo = Foo()
    foo.x = 456

    assert foo.x == 123
    assert Foo.x == 123
    # without using a class descriptior it is not
    # possible to actually stop the attribute values
    # from being changed. rather, the attribute value
    # is stored internally in the new singleton type
    assert foo._block_change is False
    assert Foo._block_change is False


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
def test__prevents_instance_attribute_changes_when_configured_with_blocking_values(
    block_value: Any,
):
    class Foo(metaclass=Singleton):
        _block_change = block_value

    foo = Foo()

    # setattr is ignore when _block_change is True
    setattr(foo, "x", 123)

    with pytest.raises(AttributeError):
        getattr(foo, "x")


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


def test__allows_attribute_deletion_when_configured_with_non_blocking_value():
    class Foo(metaclass=Singleton):
        _block_change = False
        x: int = 123

    foo = Foo()

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


def test__raises_attribute_error_when_deleted_attribute_is_accessed_when_block_change_is_false():
    class Foo(metaclass=Singleton):
        _block_change = False

    foo = Foo()

    setattr(foo, "x", "456")
    delattr(foo, "x")

    with pytest.raises(AttributeError):
        getattr(foo, "x")


@pytest.mark.parametrize("block_change", [True, False, None])
def test__prevents_arbitrary_class_attribute_deletion_on_instances(
    block_change: bool | None,
):
    class Foo(metaclass=Singleton):
        _block_change = block_change
        _arbitrary = True

    foo = Foo()

    # when _block_change is True, deletion is ignored
    if block_change or block_change is None:
        del foo._arbitrary
        delattr(foo, "_arbitrary")
    else:
        with pytest.raises(AttributeError):
            del foo._arbitrary

        with pytest.raises(AttributeError):
            delattr(foo, "_arbitrary")

    assert hasattr(foo, "_arbitrary")
    assert hasattr(Foo, "_arbitrary")


@pytest.mark.parametrize("block_change", [True, False, None])
def test__allows_arbitrary_class_attribute_deletion_on_classes(
    block_change: bool | None,
):
    class Foo(metaclass=Singleton):
        _block_change = block_change
        _arbitrary = True

    foo = Foo()

    # This cannot be intercepted, even
    # by the `__delete__` descriptor.
    # As such, it is always allowed.
    del Foo._arbitrary

    assert not hasattr(foo, "_arbitrary")
    assert not hasattr(Foo, "_arbitrary")


@pytest.mark.parametrize("block_change", [True, False, None])
def test__allows_or_prevents_arbitrary_instance_attribute_without_setting_class_attribute(
    block_change: bool | None,
):
    class Foo(metaclass=Singleton):
        _block_change = block_change

    foo = Foo()

    setattr(foo, "y", 123)

    if block_change or block_change is None:
        assert not hasattr(foo, "y")
    else:
        assert hasattr(foo, "y")
        assert getattr(foo, "y") == 123

    assert not hasattr(Foo, "y")
