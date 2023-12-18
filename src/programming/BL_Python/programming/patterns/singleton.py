# pylint: disable=C0103
# pylint: disable=E1003
# pylint: disable=W0613
# pylint: disable=C0204
""" Module containg Singleton metaclass """

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

    In addition to making a class a Singleton, these classes cannot have their attributes changed.
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
            if _instance is None:
                _instance = cast(Any, super(_new_type, cls)).__new__(cls)
                child_init = _instance.__init__

                def __init__(cls: _SingletonType, *args: Any, **kwargs: Any):
                    child_init(*args, **kwargs)
                    cls._block_change = True

                def __setattr__(self: _SingletonType, name: str, value: Any):
                    if hasattr(self, "_block_change") and self._block_change:
                        return
                    object.__setattr__(self, name, value)

                def __delattr__(self: _SingletonType, name: str):
                    if hasattr(self, "_block_change") and self._block_change:
                        return
                    object.__delattr__(self, name)

                _new_type.__init__ = __init__
                _new_type.__setattr__ = __setattr__
                _new_type.__delattr__ = __delattr__
            return _instance

        _new_type.__new__ = __new__
        return _new_type
