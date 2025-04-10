import re
from typing import Any

from typing_extensions import overload

SAFE_STRING_PATTERN = r"[^a-zA-Z0-9_.\s-]"
safe_string_regex = re.compile(SAFE_STRING_PATTERN)
SAFE_COMMA_SEPARATED_STRING_PATTERN = r"[^a-zA-Z0-9_,.\s-]"
safe_comma_separated_string_regex = re.compile(SAFE_COMMA_SEPARATED_STRING_PATTERN)


@overload
def string(value: str) -> str | None:
    """
    Remove all characters from a string that are not
    whitelisted in the `SAFE_STRING_PATTERN` regex.

    :param str value: The string to sanitize.
    :return string: The sanitized string, or `None` if the
      string only consists of invalid characters.
    """


@overload
def string(value: str, *, comma_separated: bool) -> str | None:
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
    """


def string_from_csv(value: str) -> str | None:
    """
    This method is a pass-through for `string(value, comma_separated=True)`.

    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    The string is comma-separated and this method accepts `,` as valid.

    :param str value: The string to sanitize.
    :return string: The sanitized string, or `None` if the
      string only consists of invalid characters.
    """
    return string(value, comma_separated=True)


@overload
def string(value: str, *, vector: bool) -> str | None:
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
    """


def vector_from_csv(value: str) -> str | None:
    """
    This method is a pass-through for `string(value, vector=True)`.

    Remove all characters from a string that are not
    whitelisted in the `SAFE_COMMA_SEPARATED_STRING_PATTERN` regex.

    The string is comma-separated
      and this method accepts `,` as valid. This method
      returns a string value formatted as an R vector `c(...)`
      containing the values from the CSV `value` string.

    :param str value: The string to sanitize.
    :return str | None: The vectorized CSV string, or `None` if no valid characters were found
    """
    return string(value, vector=True)


def string(
    value: str, *, comma_separated: bool = False, vector: bool = False
) -> str | None:
    if value == "":
        return value if not vector else "c()"

    if comma_separated or vector:
        if not (safe_str := safe_comma_separated_string_regex.sub("", value)):
            # if the safe_str is empty but value is not,
            # then all characters were stripped and the
            # supplied value is not "safe." Return None
            # because this is invalid.
            return None
        items = [item for item in safe_str.split(",") if item]
        new_csv_string = ("'" + "','".join(items) + "'") if items else None

        if new_csv_string is None:
            return None

        if vector:
            return f"c({new_csv_string})"
        else:
            return new_csv_string
    else:
        if not (safe_str := safe_string_regex.sub("", value)):
            return None

    return safe_str


def boolean(value: str | None) -> str:
    """
    Returns the R string `"TRUE"` or `"FALSE"` from the Python
    string `"True"` or `"False`" (lowercased), respectively.
    If `value` is `None`, "FALSE" is returned.

    :param str value: The input string containing the values `"True"` or `"False"`.
    :return str: The R string `"TRUE"` or `"FALSE"`.
    """
    return "TRUE" if (value is not None and value.lower() == "true") else "FALSE"


def vector_from_parts(
    parts: dict[str, Any],
    new_part_key: str,
    existing_part_keys: list[str],
    default: Any = "__NULL__",
) -> None:
    """
    Add a new key to the `parts` dictionary named `new_part_key`.
    The value of the new key is:
    * A Python string representing and R vector `"c(...)"` where each value
      comes from the `parts` dictionary for each key in the `existing_part_keys` list.
    * If every value from the `parts` dictionary is `None` or an empty string,
      the new key's value is the values of `default`.

    Each key in `existing_part_keys` is deleted from the `parts` dictionary.

    :param dict[str, Any] parts: A dictionary of parameters
    :param str new_part_key: The name of the new key to add to the dictionary
    :param list[str] existing_part_keys: The names of the keys from which to create the value of the new key
    :param Any default: The default value of the new key if all key values in `parts` for the keys `existing_part_keys`
      are `None` or an empty string, defaults to "__NULL__"
    """
    part_values: list[str | None] = []
    for part in existing_part_keys:
        part_values.append(str(parts[part]) if parts[part] is not None else None)
        del parts[part]

    if all([value is None or value == "" for value in part_values]):
        parts[new_part_key] = default
    else:
        serialized_part_values = "','".join([
            "__NULL__" if part_value is None else part_value
            for part_value in part_values
        ])
        parts[new_part_key] = f"c('{serialized_part_values}')"
