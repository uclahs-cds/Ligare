# pyright: reportPrivateUsage=false,reportUnusedImport=false
from typing import Any

from Ligare.programming.R.type_conversion import (
    NULL,
    Composite,
    SerializedType,
    Vector,
    _boolean,
    _convert,
    _number,
    _string,
)
from typing_extensions import overload


@overload
def string(value: str | None) -> str | None:
    """
    Remove all characters from a string that are not
    whitelisted in the `SAFE_STRING_PATTERN` regex.

    :param str value: The string to sanitize.
    :return string: The sanitized string, or `None` if the
      string only consists of invalid characters.

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import vector_from_csv

    .. doctest::

       >>> string("abc")
       'abc'

       >>> string("a,b,c")
       'abc'

       >>> string(None) is None
       True

       >>> string("\t,\t")
       '\t\t'

       >>> string(",") is None
       True

    """


@overload
def string(value: str | None, *, comma_separated: bool) -> str | None:
    """
    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    :param str value: The string to sanitize.
    :param bool comma_separated: Whether the string is comma-separated
      and this method accepts `,` as valid. If False, this method
      falls back to `string(value)`.
    :return str | None: _description_
    :return string: The sanitized string, or `None` if the
      string only consists of invalid characters.

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import vector_from_csv

    .. doctest::

       >>> string("abc")
       'abc'

       >>> string("a,b,c")
       'abc'

       >>> string(None) is None
       True

       >>> string("\t,\t")
       '\t\t'

       >>> string(",") is None
       True

    """


@overload
def string(value: str | None, *, vector: bool) -> str | None:
    """
    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    :param str value: The string to sanitize.
    :param bool vector: Whether the string is comma-separated
      and this method accepts `,` as valid. This method
      returns a string value formatted as an R vector `c(...)`
      containing the values from the CSV `value` string.
      If False, this method falls back to `string(value)`.
    :return str | None: The vectorized CSV string, or `None` if no valid
      characters were found

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import string

    .. doctest::

       >>> string("abc")
       'abc'

       >>> string("a,b,c")
       'abc'

       >>> string(None) is None
       True

       >>> string("\t,\t")
       '\t\t'

       >>> string(",") is None
       True
    """


def string(
    value: str | None, comma_separated: bool = False, vector: bool = False
) -> str | None:
    return _string(value, comma_separated=comma_separated, vector=vector).serialize()


@overload
def number(value: str | int | float | complex | None) -> str | None: ...
@overload
def number(
    value: str | int | float | complex | None, *, comma_separated: bool
) -> str | None: ...
@overload
def number(
    value: str | int | float | complex | None, *, vector: bool
) -> str | None: ...


def number(
    value: str | int | float | complex | None,
    *,
    comma_separated: bool = False,
    vector: bool = False,
) -> str | None:
    return _number(value, comma_separated=comma_separated, vector=vector).serialize()


def boolean(value: str | bool | None) -> str | None:
    """
    Returns the R string `"TRUE"` or `"FALSE"` from the Python
    strings `"True"`, `"T"`, `"False`", or `"F"` (lowercased),
    or boolean `True` or `False`, respectively.
    If `value` is `None`, `"FALSE"` is returned.

    :param str value: The input string `"True"`, `"T"`, `"False"`, or `"F"`, or boolean `True` or `False`.
    :return str: The R string `"TRUE"` or `"FALSE"`.

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import boolean

    .. doctest::

       >>> boolean(True)
       'TRUE'

       >>> boolean("True")
       'TRUE'

       >>> boolean("T")
       'TRUE'

       >>> boolean("true")
       'TRUE'

       >>> boolean(False)
       'FALSE'

       >>> boolean("False")
       'FALSE'

       >>> boolean("F")
       'FALSE'

       >>> boolean("false")
       'FALSE'

       >>> boolean(1)
       'FALSE'

       >>> boolean(0)
       'FALSE'

       >>> boolean(None)
       'FALSE'
    """
    return _boolean(value).serialize()


def composite_type_from_parts(
    composite_type: type[Composite],
    parts: dict[str, str | bool | int | float | SerializedType | None],
    new_part_key: str,
    existing_part_keys: list[str],
    default: Any = NULL,
) -> None:
    """
    Add a new key to the `parts` dictionary named `new_part_key`.

    The value of the new key is:

    * A Python string representing an R vector ``"c(...)"`` where each value
      comes from the `parts` dictionary for each key in the `existing_part_keys` list.
    * If every value from the `parts` dictionary is `None` or an empty string,
      the new key's value is the values of `default`.

    Each key in `existing_part_keys` is deleted from the `parts` dictionary.

    :param dict[str, Any] parts: A dictionary of parameters
    :param str new_part_key: The name of the new key to add to the dictionary
    :param list[str] existing_part_keys: The names of the keys from which to create the value of the new key
    :param Any default: The default value of the new key if all key values in `parts` for the keys `existing_part_keys`
      are `None` or an empty string, defaults to "__NULL__"

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import vector_from_parts

    **Convert two keys with values into a single two-item vector.**
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. doctest::

       >>> query_params = {
       ...     "scale.bar.coords.x": 0.5,
       ...     "scale.bar.coords.y": 1.0
       ... }
       >>> vector_from_parts(
       ...     query_params,
       ...     "scale.bar.coords",
       ...     ["scale.bar.coords.x", "scale.bar.coords.y"]
       ... )
       >>> query_params
       {'scale.bar.coords': 'c(0.5,1.0)'}

    **Convert two keys with numerical and string values into a single two-item vector.**
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. doctest::

       >>> query_params = {
       ...     "scale.bar.coords.x": 0.5,
       ...     "scale.bar.coords.y": '1.0'
       ... }
       >>> vector_from_parts(
       ...     query_params,
       ...     "scale.bar.coords",
       ...     ["scale.bar.coords.x", "scale.bar.coords.y"]
       ... )
       >>> query_params
       {'scale.bar.coords': "c(0.5,'1.0')"}

    **Convert two keys into a single two-item vector where one value is `None`**
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. doctest::

       >>> query_params = {
       ...     "scale.bar.coords.x": 0.5,
       ...     "scale.bar.coords.y": None
       ... }
       >>> vector_from_parts(
       ...     query_params,
       ...     "scale.bar.coords",
       ...     ["scale.bar.coords.x", "scale.bar.coords.y"]
       ... )
       >>> query_params
       {'scale.bar.coords': "c(0.5,'__NULL__')"}

    **Convert two keys into an empty value where all values are `None`**
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. doctest::

       >>> query_params = {
       ...     "scale.bar.coords.x": None,
       ...     "scale.bar.coords.y": None
       ... }
       >>> vector_from_parts(
       ...     query_params,
       ...     "scale.bar.coords",
       ...     ["scale.bar.coords.x", "scale.bar.coords.y"]
       ... )
       >>> query_params
       {'scale.bar.coords': '__NULL__'}

    **Convert many keys of varying types into a single vector.**
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. doctest::

       >>> query_params = {
       ...     "scale.bar.coords.x": 0.5,
       ...     "scale.bar.coords.y": '1.0',
       ...     "scale.bar.coords.z": None,
       ...     "scale.bar.coords.a": 123,
       ...     "scale.bar.coords.b": True,
       ...     "scale.bar.coords.c": False
       ... }
       >>> vector_from_parts(
       ...     query_params,
       ...     "scale.bar.coords",
       ...     [
       ...         "scale.bar.coords.x",
       ...         "scale.bar.coords.y",
       ...         "scale.bar.coords.z",
       ...         "scale.bar.coords.a",
       ...         "scale.bar.coords.b",
       ...         "scale.bar.coords.c",
       ...     ]
       ... )
       >>> query_params
       {'scale.bar.coords': "c(0.5,'1.0','__NULL__',123,'TRUE','FALSE')"}
    """
    if not isinstance(parts, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError(
            f"`parts` must be a dictionary. The value given is a `{type(parts)}`."
        )

    part_values: list[SerializedType | None] = []
    for part in existing_part_keys:
        part_values.append(_convert(parts.get(part)))
        del parts[part]

    if all([value is None or value.serialize() in {"", NULL} for value in part_values]):
        parts[new_part_key] = default
    else:
        parts[new_part_key] = composite_type(part_values).serialize() or NULL


def from_parts(
    parts: dict[str, str | bool | int | float | SerializedType | None],
    new_part_key: str,
    existing_part_keys: list[str],
    default: Any = NULL,
    composite_type: type[Composite] = Vector,
) -> None:
    if not isinstance(parts, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError()

    for k, v in {k: parts[k] for k in existing_part_keys}.items():
        parts[k] = _convert(v, make_vector=True)

    return composite_type_from_parts(
        composite_type, parts, new_part_key, existing_part_keys, default
    )


def number_from_parts(
    parts: dict[str, Any],
    new_part_key: str,
    existing_part_keys: list[str],
    default: Any = NULL,
    composite_type: type[Composite] = Vector,
) -> None:
    for key in existing_part_keys:
        if not isinstance(parts[key], bool):
            parts[key] = _number(parts[key], vector=True)
    return composite_type_from_parts(
        composite_type, parts, new_part_key, existing_part_keys, default
    )


def string_from_parts(
    parts: dict[str, Any],
    new_part_key: str,
    existing_part_keys: list[str],
    default: Any = NULL,
    composite_type: type[Composite] = Vector,
) -> None:
    for key in existing_part_keys:
        parts[key] = _string(parts[key], vector=True)
    return composite_type_from_parts(
        composite_type, parts, new_part_key, existing_part_keys, default
    )


def string_from_csv(value: str | None) -> str | None:
    """
    This method is a pass-through for `string(value, comma_separated=True)`.

    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    The string is comma-separated and this method accepts `,` as valid.

    :param str value: The string to sanitize.
    :return string: The sanitized string, or `None` if the
      string only consists of invalid characters.

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import string_from_csv

    .. doctest::

       >>> string_from_csv("abc")
       "'abc'"

       >>> string_from_csv("a,b,c")
       "'a','b','c'"

       >>> string_from_csv(None) is None
       True

       >>> string_from_csv("\\t,\\t")
       "'\\t','\\t'"

       >>> string_from_csv(",") is None
       True

    """
    return string(value, comma_separated=True)


def number_from_csv(value: str | None) -> str | None:
    """
    This method is a pass-through for `number(value, comma_separated=True)`.

    Remove all characters from a string of numbers that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    The string is comma-separated and this method accepts `,` as valid.

    :param str value: The string to sanitize.
    :return string: The sanitized string, or `None` if the
      string only consists of invalid characters.

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import string_from_csv

    .. doctest::

       >>> number_from_csv("123")
       "123"

       >>> number_from_csv("1,2,3")
       "1,2,3"

       >>> number_from_csv(None) is None
       True

       >>> number_from_csv(",") is None
       True

    """
    return number(value, comma_separated=True)


def string_vector_from_csv(value: str | None) -> str | None:
    """
    This method is a pass-through for `string(value, vector=True)`.

    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    The string is comma-separated
      and this method accepts `,` as valid. This method
      returns a string value formatted as an R vector `c(...)`
      containing the string values from the CSV `value` string.

    :param str value: The string to sanitize.
    :return str | None: The vectorized CSV string, or `None` if no valid characters were found

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import string_vector_from_csv

    .. doctest::

       >>> string_vector_from_csv("'").value is None
       True

       >>> string_vector_from_csv("''").value is None
       True

       >>> string_vector_from_csv("'a'").value
       "c('a')"

       >>> string_vector_from_csv("a-b-c").value
       "c('a-b-c')"

       >>> string_vector_from_csv("a-b-.c").value
       "c('a-b-.c')"

       >>> string_vector_from_csv("a-b-^%^$%^c").value
       "c('a-b-c')"

       >>> string_vector_from_csv("").value
       'c()'

       >>> string_vector_from_csv("abc").value
       "c('abc')"

       >>> string_vector_from_csv("a,b,c").value
       "c('a','b','c')"

       >>> string_vector_from_csv(None).value
       'c()'

       >>> string_vector_from_csv("!!!").value is None
       True

       >>> string_vector_from_csv("a!b!c!").value
       "c('abc')"

       >>> string_vector_from_csv("a!,b!,c!").value
       "c('a','b','c')"

       >>> string_vector_from_csv("a,b,c,").value
       "c('a','b','c')"

       >>> string_vector_from_csv("a.b.c").value
       "c('a.b.c')"
    """
    return string(value, vector=True)


def number_vector_from_csv(value: str | None) -> str | None:
    """
    This method is a pass-through for `number(value, vector=True)`.

    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    The string is comma-separated
      and this method accepts `,` as valid. This method
      returns a string value formatted as an R vector `c(...)`
      containing the numerical values from the CSV `value` string.

    :param str value: The string to sanitize.
    :return str | None: The vectorized CSV string, or `None` if no valid characters were found

    ----

    ---------
    **Usage**
    ---------

    .. testsetup::

       from Ligare.programming.R.type_conversion import number_vector_from_csv

    .. doctest::

       >>> number_vector_from_csv("'").value is None
       True

       >>> number_vector_from_csv("''").value is None
       True

       >>> number_vector_from_csv("'a'")
       Traceback (most recent call last):
        ...
       ValueError: Failed to convert the value `'a'` to a number or number vector. Other parameters: comma_separated=False, vector=True

       >>> number_vector_from_csv("a")
       Traceback (most recent call last):
        ...
       ValueError: Failed to convert the value `a` to a number or number vector. Other parameters: comma_separated=False, vector=True

       >>> number_vector_from_csv("").value
       'c()'

       >>> number_vector_from_csv("123").value
       'c(123)'

       >>> number_vector_from_csv("1,2,3").value
       'c(1,2,3)'

       >>> number_vector_from_csv(None).value
       'c()'

       >>> number_vector_from_csv("!!!").value is None
       True

       >>> number_vector_from_csv("1!2!3!").value
       'c(123)'

       >>> number_vector_from_csv("1!,2!,3!").value
       'c(1,2,3)'

       >>> number_vector_from_csv("1,2,3,").value
       'c(1,2,3)'
    """
    return number(value, vector=True)
