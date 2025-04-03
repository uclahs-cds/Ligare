# pylint: disable=C0103
# pylint: disable=E1003
# pylint: disable=W0613
# pylint: disable=C0204
"""Module containg Singleton metaclass"""

# pyright: reportPrivateUsage=false

from typing import Any, NewType, Type, cast, final


class _Singleton(Type[Any]):
    _block_change: bool = False


_SingletonType = NewType("_SingletonType", _Singleton)


@final
class Singleton(type):
    """
    Singleton metaclass.

    To create a new Singleton class, set the metaclass of your class to `Singleton`:

    .. code-block:: python

        class Foo(metaclass=Singleton):
            pass

    **Behavior**:
    By default, Singleton classes prevent attribute modifications. To allow attribute modifications,
    define an attribute named `_block_change` in the class and set it to `False`.
    Not defining this attribute, or setting any other value, will enforce the default behavior.

    **Warning**:
    Setting `_block_change = False` disables attribute protection, and `Singleton` is **not** thread-safe
    in this configuration. Additionally, it is not possible to prevent the deletion of _class_ attributes.

    **Examples**:
    The following classes are all equivalent:

    .. code-block:: python

        class Foo(metaclass=Singleton):
            pass

        class Foo(metaclass=Singleton):
            _block_change = True

        class Foo(metaclass=Singleton):
            _block_change = None

        class Foo(metaclass=Singleton):
            _block_change = 123

    To enable attribute modifications:

    .. code-block:: python

        class Foo(metaclass=Singleton):
            _block_change = False
    """

    class InstanceValue:
        __value: Any
        __deleted: bool

        def __init__(self, value: Any) -> None:  # pyright: ignore[reportMissingSuperCall]
            self.__value = value
            self.__deleted = False

        @property
        def value(self):
            return self.__value

        @value.deleter
        def value(self):
            self.__deleted = True

        @property
        def deleted(self):
            return self.__deleted

    def __new__(
        cls: "type[Singleton]",
        cls_name: str,
        bases: tuple[Type[Any]],
        members: dict[str, Any],
    ):
        _new_type: Type[Any] = type(cls_name, bases, members)
        _instance: _SingletonType | None = None
        BLOCK_CHANGE_ATTR_NAME = "_block_change"
        _block_change: bool | None = None

        def __new__(cls: Any, *args: Any, **kwargs: Any):
            nonlocal _instance

            if _instance is None:
                _instance = cast(Any, super(_new_type, cls)).__new__(cls)
                child_init = _instance.__init__

                def __init__(cls: _SingletonType, *args: Any, **kwargs: Any):
                    nonlocal _block_change

                    child_init(*args, **kwargs)

                _new_type.__init__ = __init__

                def __getattribute__(self: _SingletonType, name: str) -> Any:
                    value = super(cls, self).__getattribute__(name)
                    if isinstance(value, Singleton.InstanceValue):
                        if value.deleted:
                            raise AttributeError(self, name)
                        return value.value
                    return value

                def __setattr__(self: _SingletonType, name: str, value: Any):
                    nonlocal _block_change

                    if _block_change or (
                        hasattr(self, BLOCK_CHANGE_ATTR_NAME) and self._block_change
                    ):
                        return

                    if hasattr(cls, name):
                        object.__setattr__(self, name, value)
                    else:
                        object.__setattr__(self, name, Singleton.InstanceValue(value))

                def __delattr__(self: _SingletonType, name: str):
                    nonlocal _block_change

                    if _block_change or getattr(self, BLOCK_CHANGE_ATTR_NAME, True):
                        return

                    value = super(cls, self).__getattribute__(name)
                    if isinstance(value, Singleton.InstanceValue):
                        del value.value
                    else:
                        object.__delattr__(self, name)

                _new_type.__setattr__ = __setattr__  # pyright: ignore[reportAttributeAccessIssue]
                _new_type.__delattr__ = __delattr__  # pyright: ignore[reportAttributeAccessIssue]
                _new_type.__getattribute__ = __getattribute__  # pyright: ignore[reportAttributeAccessIssue]

            return _instance

        block_change = getattr(_new_type, BLOCK_CHANGE_ATTR_NAME, True)
        _block_change = block_change is None or block_change is not False
        cls._block_change = _block_change
        _new_type.__new__ = __new__  # pyright: ignore[reportAttributeAccessIssue]
        return _new_type
