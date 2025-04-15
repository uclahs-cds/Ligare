from typing import Any

import pytest
from Ligare.programming.R.type_conversion import (
    boolean,
    string,
    string_from_csv,
    vector_from_csv,
    vector_from_parts,
)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("abc", "abc"),
        ("c('a','b','c')", "cabc"),
        ("123", "123"),
        ("a'b'c", "abc"),
        ("'1,2,3'", "123"),
        ("", ""),
        (" ", " "),
        ("\t", "\t"),
        (None, None),
    ],
)
def test__string__returns_sanitized_string(input_value: Any, expected_value: str):
    result = string(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, TypeError),
        (True, TypeError),
        (0, TypeError),
    ],
)
def test__string__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = string(input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("a,b,c", "'a','b','c'"),
        ("c('a','b','c')", "'ca','b','c'"),
        ("1,2,3", "'1','2','3'"),
        ("a,'b,'c", "'a','b','c'"),
        ("'1,2,3'", "'1','2','3'"),
        ("a,", "'a'"),
        ("a,b,", "'a','b'"),
        ("", ""),
        (" ", "' '"),
        ("\t", "'\t'"),
        (",", None),
        (" , ", "' ',' '"),
        ("\t,\t", "'\t','\t'"),
        (None, None),
    ],
)
def test__string__csv__returns_sanitized_csv_string(
    input_value: Any, expected_value: str
):
    result = string(input_value, comma_separated=True)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, TypeError),
        (True, TypeError),
        (0, TypeError),
    ],
)
def test__string__csv__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = string(input_value, comma_separated=True)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("a,b,c", "'a','b','c'"),
        ("c('a','b','c')", "'ca','b','c'"),
        ("1,2,3", "'1','2','3'"),
        ("a,'b,'c", "'a','b','c'"),
        ("'1,2,3'", "'1','2','3'"),
        ("a,", "'a'"),
        ("a,b,", "'a','b'"),
        ("", ""),
        (" ", "' '"),
        ("\t", "'\t'"),
        (",", None),
        (" , ", "' ',' '"),
        ("\t,\t", "'\t','\t'"),
        (None, None),
    ],
)
def test__string_from_csv__returns_sanitized_csv_string(
    input_value: Any, expected_value: str
):
    result = string_from_csv(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, TypeError),
        (True, TypeError),
        (0, TypeError),
    ],
)
def test__string_from_csv__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = string_from_csv(input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("a,b,c", "c('a','b','c')"),
        ("c('a','b','c')", "c('ca','b','c')"),
        ("1,2,3", "c('1','2','3')"),
        ("a,'b,'c", "c('a','b','c')"),
        ("'1,2,3'", "c('1','2','3')"),
        ("a,", "c('a')"),
        ("a,b,", "c('a','b')"),
        ("", "c()"),
        (" ", "c(' ')"),
        ("\t", "c('\t')"),
        (",", None),
        (" , ", "c(' ',' ')"),
        ("\t,\t", "c('\t','\t')"),
        (None, "c()"),
    ],
)
def test__string__vector__returns_sanitized_vector_string(
    input_value: Any, expected_value: str
):
    result = string(input_value, vector=True)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, TypeError),
        (True, TypeError),
        (0, TypeError),
    ],
)
def test__string__vector__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = string(input_value, vector=True)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("a,b,c", "c('a','b','c')"),
        ("c('a','b','c')", "c('ca','b','c')"),
        ("1,2,3", "c('1','2','3')"),
        ("a,'b,'c", "c('a','b','c')"),
        ("'1,2,3'", "c('1','2','3')"),
        ("a,", "c('a')"),
        ("a,b,", "c('a','b')"),
        ("", "c()"),
        (" ", "c(' ')"),
        ("\t", "c('\t')"),
        (",", None),
        (" , ", "c(' ',' ')"),
        ("\t,\t", "c('\t','\t')"),
        (None, "c()"),
    ],
)
def test__vector_from_csv__returns_sanitized_vector_string(
    input_value: Any, expected_value: str
):
    result = vector_from_csv(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, TypeError),
        (True, TypeError),
        (0, TypeError),
    ],
)
def test__vector_from_csv__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = vector_from_csv(input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("True", "TRUE"),
        ("TRUE", "TRUE"),
        ("true", "TRUE"),
        ("False", "FALSE"),
        ("FALSE", "FALSE"),
        ("false", "FALSE"),
        ("", "FALSE"),
        (" ", "FALSE"),
        ("abc123", "FALSE"),
        (None, "FALSE"),
    ],
)
def test__boolean__returns_sanitized_string(input_value: Any, expected_value: str):
    result = boolean(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "parts,new_part_key,existing_part_keys,expected_value",
    [
        ({"a": 1, "b": 2}, "c", ["a", "b"], {"c": "c('1','2')"}),
        ({"a": 1, "b": 2, "c": 3}, "c", ["a", "b"], {"c": "c('1','2')"}),
        ({"a": 1, "b": 2}, "a", ["a", "b"], {"a": "c('1','2')"}),
        ({"a": 1, "b": 2, "c": 3}, "a", ["a", "b"], {"a": "c('1','2')", "c": 3}),
        ({1: 1, 2: 2}, 3, [1, 2], {3: "c('1','2')"}),
        ({"a": None, "b": None}, "c", ["a", "b"], {"c": "__NULL__"}),
    ],
)
def test__vector_from_parts__returns(
    parts: dict[Any, Any],
    new_part_key: Any,
    existing_part_keys: list[Any],
    expected_value: dict[Any, Any],
):
    vector_from_parts(parts, new_part_key, existing_part_keys)
    assert parts == expected_value


@pytest.mark.parametrize(
    "parts,new_part_key,existing_part_keys,expected_value",
    [
        (None, "c", ["a", "b"], TypeError),
        ("", "c", ["a", "b"], TypeError),
        (" ", "c", ["a", "b"], TypeError),
        (1, "c", ["a", "b"], TypeError),
        ([], "c", ["a", "b"], TypeError),
        ((), "c", ["a", "b"], TypeError),
        (set(), "c", ["a", "b"], TypeError),
    ],  # pyright: ignore[reportUnknownArgumentType]
)
def test__vector_from_parts__raises_when_parts_is_not_a_dict(
    parts: Any,
    new_part_key: Any,
    existing_part_keys: list[Any],
    expected_value: type[Exception],
):
    with pytest.raises(expected_value):
        vector_from_parts(parts, new_part_key, existing_part_keys)
