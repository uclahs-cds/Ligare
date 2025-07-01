# pyright: reportUnusedFunction=false
import re
from enum import Enum
from typing import Any, Protocol

from typing_extensions import overload, override

SAFE_STRING_PATTERN = r"[^a-zA-Z0-9_.\s-]"
safe_string_regex = re.compile(SAFE_STRING_PATTERN)
SAFE_COMMA_SEPARATED_STRING_PATTERN = r"[^a-zA-Z0-9_,.\s-]"
safe_comma_separated_string_regex = re.compile(SAFE_COMMA_SEPARATED_STRING_PATTERN)


NULL = "__NULL__"
FALSE = "FALSE"
TRUE = "TRUE"


class SerializedType:
    def __init__(self, value: Any) -> None:
        super().__init__()
        self.value = value

    def serialize(self) -> str | None:
        if self.value is None:
            return NULL
        return str(self.value)


class Number(SerializedType):
    def __init__(self, value: Any) -> None:
        if (
            (value is None or value == NULL)
            or (isinstance(value, int) and not isinstance(value, bool))
            or isinstance(value, float)
            or isinstance(value, complex)
        ):
            super().__init__(value)
        elif not value:
            super().__init__(None)
        else:
            try:
                super().__init__(int(value))
            except Exception:
                super().__init__(float(value))


class Boolean(SerializedType):
    @override
    def serialize(self) -> str | None:
        return (
            TRUE
            if (self.value is not None and str(self.value).lower() in ["true", "t"])
            else FALSE
        )


class String(SerializedType):
    @override
    def serialize(self) -> str | None:
        if self.value is None:
            return NULL
        if getattr(self.value, "translate", None):
            translated = self.value.translate(str.maketrans({"'": r"\'"}))
            return f"'{translated}'"
        else:
            return f"'{self.value}'"


class CompositeType(Enum):
    VECTOR = "c"
    LIST = "list"
    SEQ = "seq"


class Composite(SerializedType):
    composite_type: CompositeType | None = None
    value: list[SerializedType] | None

    def __init__(self, value: "list[SerializedType | None] | Composite | None") -> None:
        if value is not None and type(value) == Composite:
            # because bare Composite types don't have a serialized
            # type, if the value passed into the ctor is itself a
            # `Composite`, then we just convert the type of the
            # composite, basically "masking" the containing composite.
            super().__init__(value.value)
        else:
            super().__init__(value)

    @override
    def serialize(self) -> str:
        if self.value is None:
            return NULL

        if not isinstance(self.value, Composite):
            serialized_values = ",".join([
                (
                    (value.serialize() or NULL)
                    if value is not None  # pyright: ignore[reportUnnecessaryComparison]
                    else NULL
                )
                for value in self.value
            ])
        else:
            serialized_values = self.value.serialize()

        if self.composite_type:
            return f"{self.composite_type.value}({serialized_values})"
        else:
            return str(serialized_values)


class Vector(Composite):
    composite_type = CompositeType.VECTOR


class List(Composite):
    composite_type = CompositeType.LIST


class Seq(Composite):
    composite_type = CompositeType.SEQ


class Converter(Protocol):
    @overload
    def __call__(self, value: str | None) -> SerializedType: ...
    @overload
    def __call__(
        self, value: str | None, *, comma_separated: bool
    ) -> String | Composite: ...
    @overload
    def __call__(self, value: str | None, *, vector: bool) -> Vector: ...

    def __call__(
        self, value: str | None, *, comma_separated: bool = False, vector: bool = False
    ) -> SerializedType: ...


def _string(
    value: str | None, *, comma_separated: bool = False, vector: bool = False
) -> Vector | Composite | String:
    if value is None:
        return String(None)

    if value == "":
        if comma_separated:
            return Composite([String(value)])
        if vector:
            return Vector([])
        return String(value)

    try:
        if comma_separated or vector:
            if not (safe_str := safe_comma_separated_string_regex.sub("", value)):
                # if the safe_str is empty but value is not,
                # then all characters were stripped and the
                # supplied value is not "safe." Return None
                # because this is invalid.
                return String(None)

            items = (item for item in safe_str.split(","))
            if vector:
                return Vector([String(item) for item in items])
            else:
                return Composite([String(item) for item in items])
        else:
            if not (safe_str := safe_string_regex.sub("", value)):
                return String(None)

        return String(safe_str)
    except Exception as e:
        raise type(e)(
            f"Failed to convert the value `{value}` to a string. Other parameters: {comma_separated=}, {vector=}"
        ) from e


@overload
def string(value: str | None) -> String: ...


@overload
def string(value: str | None, *, comma_separated: bool) -> Composite | String: ...


@overload
def string(value: str | None, *, vector: bool) -> Vector | String: ...


def string(
    value: str | None, *, comma_separated: bool = False, vector: bool = False
) -> Vector | Composite | String:
    return _string(value, comma_separated=comma_separated, vector=vector)


def _number(
    value: str | int | float | complex | None,
    *,
    comma_separated: bool = False,
    vector: bool = False,
) -> Vector | Number | Composite:
    if isinstance(value, bool):
        raise ValueError("Disallowed type `bool` for 'number' serialization.")

    if isinstance(value, int) or isinstance(value, float) or isinstance(value, complex):
        return Number(value)

    if value == "" or value is None or value == NULL:
        return Number(value)

    try:
        if comma_separated or vector:
            if not (safe_str := safe_comma_separated_string_regex.sub("", str(value))):
                # if the safe_str is empty but value is not,
                # then all characters were stripped and the
                # supplied value is not "safe." Return None
                # because this is invalid.
                # return None
                return Number(None)
            items = (
                item
                for item in filter(lambda element: element, safe_str.split(","))
                if float(item) or float(item) == 0
            )

            if vector:
                return Vector([Number(item) for item in items])
            else:
                return Composite([Number(item) for item in items])
        else:
            if not (safe_str := safe_string_regex.sub("", str(value))):
                return Number(None)

        return Number(safe_str)
    except Exception as e:
        raise type(e)(
            f"Failed to convert the value `{value}` to a number or number vector. Other parameters: {comma_separated=}, {vector=}"
        ) from e


@overload
def number(value: str | int | float | complex | None) -> Number: ...
@overload
def number(
    value: str | int | float | complex | None, *, comma_separated: bool
) -> Composite | Number: ...
@overload
def number(
    value: str | int | float | complex | None, *, vector: bool
) -> Vector | Composite | Number: ...


def number(
    value: str | int | float | complex | None,
    *,
    comma_separated: bool = False,
    vector: bool = False,
) -> Vector | Number | Composite:
    return _number(value, comma_separated=comma_separated, vector=vector)


def _boolean(value: str | bool | None) -> Boolean:
    return Boolean(value)


boolean = _boolean


def _convert(
    value: str | bool | int | float | SerializedType | None, make_vector: bool = False
) -> SerializedType:
    if isinstance(value, SerializedType):
        return value

    if value is None:
        return String(None)

    if isinstance(value, bool):
        return boolean(value)

    if isinstance(value, int) or isinstance(value, float):
        return number(value, vector=make_vector)

    return string(value, vector=make_vector)
