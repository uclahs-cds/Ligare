# pylint: disable=C0103
# pylint: disable=E1003
# pylint: disable=W0613
# pylint: disable=C0204
"""Module containg Singleton metaclass"""

# pyright: reportPrivateUsage=false

from typing import Any, NewType, Type, cast


class _Singleton(Type[Any]):
    _block_change: bool = False


_SingletonType = NewType("_SingletonType", _Singleton)


class Singleton(type):
    """
    Singleton metaclass.
    Create a new Singleton type by setting that class's metaclass:

    `class Foo(metaclass=Singleton): ...`

    By default, the classes created by Singleton cannot have their attributes changed.
    To change this behavior, define an attribute named `_block_change` whose value is `False`.
    Not defining this attribute, or setting any other value, uses the default behavior.
    Be _VERY CAREFUL_ when using `_block_change = False` as `Singleton` is _NOT_ threadsafe.

    For example, these are all equivalent:
    ```
    class Foo(metaclass=Singleton): ...

    class Foo(metaclass=Singleton):
        _block_change = True

    class Foo(metaclass=Singleton):
        _block_change = None

    class Foo(metaclass=Singleton):
        _block_change = 123
    ```

    While this example is how to enable changes of attributes.
    ```
    class Foo(metaclass=Singleton):
        _block_change = False
    ```
    """

    def __new__(
        cls: type,
        cls_name: str,
        bases: tuple[Type[Any]],
        members: dict[str, Any],
    ):
        _new_type: Type[Any] = type(cls_name, bases, members)
        _instance: _SingletonType | None = None

        def __new__(cls: Any, *args: Any, **kwargs: Any):
            nonlocal _instance

            block_change_attr_name = "_block_change"

            if _instance is None:
                _instance = cast(Any, super(_new_type, cls)).__new__(cls)
                child_init = _instance.__init__

                def __init__(cls: _SingletonType, *args: Any, **kwargs: Any):
                    child_init(*args, **kwargs)
                    block_change = getattr(cls, block_change_attr_name, None)

                    cls._block_change = (
                        block_change is None or block_change is not False
                    )

                _new_type.__init__ = __init__

                def __setattr__(self: _SingletonType, name: str, value: Any):
                    if hasattr(self, block_change_attr_name) and self._block_change:
                        return
                    object.__setattr__(self, name, value)

                def __delattr__(self: _SingletonType, name: str):
                    if hasattr(self, block_change_attr_name) and self._block_change:
                        return
                    object.__delattr__(self, name)

                _new_type.__setattr__ = __setattr__
                _new_type.__delattr__ = __delattr__
            return _instance

        _new_type.__new__ = __new__
        return _new_type
