from dataclasses import dataclass
from typing import Any

import pytest
from Ligare.programming.R.serializers import (
    boolean,
    from_parts,
    number,
    number_from_csv,
    number_from_parts,
    number_vector_from_csv,
    string,
    string_from_csv,
    string_from_parts,
    string_vector_from_csv,
)
from Ligare.programming.R.type_conversion import FALSE, NULL, TRUE, List, Vector


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("abc", "'abc'"),
        ("c('a','b','c')", "'cabc'"),
        ("123", "'123'"),
        ("a'b'c", "'abc'"),
        ("'1,2,3'", "'123'"),
        ("", "''"),
        (" ", "' '"),
        ("\t", "'\t'"),
        ("!!!", NULL),
        (None, NULL),
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
        ("a,", "'a',''"),
        ("a,b,", f"'a','b',''"),
        ("", "''"),
        (" ", "' '"),
        ("\t", "'\t'"),
        (",", "'',''"),
        (" , ", "' ',' '"),
        ("\t,\t", "'\t','\t'"),
        (None, NULL),
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
        ("123", "123"),
        ("1,2,3", "123"),
        ("", NULL),
        ("!!!", NULL),
        (None, NULL),
    ],
)
def test__number__returns_sanitized_number(input_value: Any, expected_value: str):
    result = number(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, ValueError),
        (True, ValueError),
        (" ", ValueError),
        ("a,b,c", ValueError),
        ("c(1,2,3)", ValueError),
    ],
)
def test__number__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = number(input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("1,2,3", "1,2,3"),
        ("'1,2,3'", "1,2,3"),
        ("1,", "1"),
        ("1,2,", f"1,2"),
        ("", NULL),
        ("!!!", NULL),
        (",", ""),
        (None, NULL),
    ],
)
def test__number__csv__returns_sanitized_csv_number(
    input_value: Any, expected_value: str
):
    result = number(input_value, comma_separated=True)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, ValueError),
        (True, ValueError),
        (" ", ValueError),
        ("a,b,c", ValueError),
        ("c(1,2,3)", ValueError),
    ],
)
def test__number__csv__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = number(input_value, comma_separated=True)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("a,b,c", "'a','b','c'"),
        ("c('a','b','c')", "'ca','b','c'"),
        ("1,2,3", "'1','2','3'"),
        ("a,'b,'c", "'a','b','c'"),
        ("'1,2,3'", "'1','2','3'"),
        ("a,", "'a',''"),
        ("a,b,", "'a','b',''"),
        ("", "''"),
        (" ", "' '"),
        ("\t", "'\t'"),
        (",", "'',''"),
        (" , ", "' ',' '"),
        ("\t,\t", "'\t','\t'"),
        (None, NULL),
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
        ("1,2,3", "1,2,3"),
        ("'1,2,3'", "1,2,3"),
        ("1,", "1"),
        ("1,2,", f"1,2"),
        ("", NULL),
        ("!!!", NULL),
        (",", ""),
        (None, NULL),
    ],
)
def test__number_from_csv__returns_sanitized_csv_string(
    input_value: Any, expected_value: str
):
    result = number_from_csv(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, ValueError),
        (True, ValueError),
        (" ", ValueError),
        ("a,b,c", ValueError),
        ("c(1,2,3)", ValueError),
    ],
)
def test__number_from_csv__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = number_from_csv(input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("a,b,c", "c('a','b','c')"),
        ("c('a','b','c')", "c('ca','b','c')"),
        ("1,2,3", "c('1','2','3')"),
        ("a,'b,'c", "c('a','b','c')"),
        ("'1,2,3'", "c('1','2','3')"),
        ("a,", "c('a','')"),
        ("a,b,", "c('a','b','')"),
        ("", "c()"),
        (" ", "c(' ')"),
        ("\t", "c('\t')"),
        (",", f"c('','')"),
        (" , ", "c(' ',' ')"),
        ("\t,\t", "c('\t','\t')"),
        ("!!!", NULL),
        (None, NULL),
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
        ("a,", "c('a','')"),
        (",a", "c('','a')"),
        ("a,b,", "c('a','b','')"),
        ("", "c()"),
        (" ", "c(' ')"),
        ("\t", "c('\t')"),
        (",", "c('','')"),
        (" , ", "c(' ',' ')"),
        ("\t,\t", "c('\t','\t')"),
        (None, NULL),
    ],
)
def test__string_vector_from_csv__returns_sanitized_vector_string(
    input_value: Any, expected_value: str
):
    result = string_vector_from_csv(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, TypeError),
        (True, TypeError),
        (0, TypeError),
    ],
)
def test__string_vector_from_csv__raises_when_input_is_not_a_str_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = string_vector_from_csv(input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        ("1,2,3", "c(1,2,3)"),
        ("1,'2,'3", "c(1,2,3)"),
        ("'1,2,3'", "c(1,2,3)"),
        ("1,", "c(1)"),
        (",1", "c(1)"),
        ("1,2,", "c(1,2)"),
        ("", NULL),
        (",", "c()"),
        (None, NULL),
    ],
)
def test__number_vector_from_csv__returns_sanitized_vector_string(
    input_value: Any, expected_value: str
):
    result = number_vector_from_csv(input_value)
    assert result == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (False, ValueError),
        (True, ValueError),
        ("c('1','2','3')", ValueError),
        ("c(1,2,3)", ValueError),
        ("a,'b,'c", ValueError),
        ("1,a,3", ValueError),
        (" ", ValueError),
        ("\t", ValueError),
        (" , ", ValueError),
        ("\t,\t", ValueError),
    ],
)
def test__number_vector_from_csv__raises_when_input_is_not_a_number_or_None(
    input_value: Any | None, expected_value: type[Exception]
):
    with pytest.raises(expected_value):
        _ = number_vector_from_csv(input_value)


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


@dataclass
class FromPartsTestData:
    parts: dict[Any, Any]
    new_part_key: Any
    existing_part_keys: list[Any]
    expected_value: dict[Any, Any]


@pytest.mark.parametrize(
    "data",
    [
        FromPartsTestData(
            parts={"a": 1, "b": 2},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "c(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2, "c": 3},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "c(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "c(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2, "c": 3},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "c(1,2)", "c": 3},
        ),
        FromPartsTestData(
            parts={1: 1, 2: 2},
            new_part_key=3,
            existing_part_keys=[1, 2],
            expected_value={3: "c(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": None, "b": None},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": NULL},
        ),
        FromPartsTestData(
            parts={"x": 0.5, "y": "1.0", "z": None, "a": 123, "b": True, "c": False},
            new_part_key="A",
            existing_part_keys=["x", "y", "z", "a", "b", "c"],
            expected_value={"A": f"c(0.5,c('1.0'),{NULL},123,{TRUE},{FALSE})"},
        ),
    ],
)
def test__vector_from_parts__returns_expected_serialized_vector(
    data: FromPartsTestData,
):
    from_parts(
        data.parts, data.new_part_key, data.existing_part_keys, composite_type=Vector
    )
    assert data.parts == data.expected_value


@pytest.mark.parametrize(
    "data",
    [
        FromPartsTestData(
            parts=None,  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
        FromPartsTestData(
            parts="",  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
        FromPartsTestData(
            parts=" ",  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
        FromPartsTestData(
            parts=1,  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
        FromPartsTestData(
            parts=[],  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
        FromPartsTestData(
            parts=(),  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
        FromPartsTestData(
            parts=set(),  # pyright: ignore[reportArgumentType]
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value=TypeError,  # pyright: ignore[reportArgumentType]
        ),
    ],
)
def test__vector_from_parts__raises_when_parts_is_not_a_dict(data: FromPartsTestData):
    with pytest.raises(data.expected_value):  # pyright: ignore[reportArgumentType]
        from_parts(
            data.parts,
            data.new_part_key,
            data.existing_part_keys,
            composite_type=Vector,
        )


@pytest.mark.parametrize(
    "data",
    [
        FromPartsTestData(
            parts={"a": 1, "b": 2},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": "1,2", "b": "3,4"},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(c('1','2'),c('3','4'))"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2, "c": 3},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2, "c": 3},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "list(1,2)", "c": 3},
        ),
        FromPartsTestData(
            parts={1: 1, 2: 2},
            new_part_key=3,
            existing_part_keys=[1, 2],
            expected_value={3: "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": None, "b": None},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": NULL},
        ),
        FromPartsTestData(
            parts={"x": 0.5, "y": "1.0", "z": None, "a": 123, "b": True, "c": False},
            new_part_key="A",
            existing_part_keys=["x", "y", "z", "a", "b", "c"],
            expected_value={"A": f"list(0.5,c('1.0'),{NULL},123,{TRUE},{FALSE})"},
        ),
    ],
)
def test__list_from_parts__returns_expected_serialized_list(data: FromPartsTestData):
    from_parts(
        data.parts, data.new_part_key, data.existing_part_keys, composite_type=List
    )
    assert data.parts == data.expected_value


@pytest.mark.parametrize(
    "data",
    [
        FromPartsTestData(
            parts={"a": 1, "b": 2},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": "1,2", "b": "3,4"},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(c(1,2),c(3,4))"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2, "c": 3},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": 1, "b": 2, "c": 3},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "list(1,2)", "c": 3},
        ),
        FromPartsTestData(
            parts={1: 1, 2: 2},
            new_part_key=3,
            existing_part_keys=[1, 2],
            expected_value={3: "list(1,2)"},
        ),
        FromPartsTestData(
            parts={"a": None, "b": None},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": NULL},
        ),
        FromPartsTestData(
            parts={"x": 0.5, "y": "1.0", "z": None, "a": 123, "b": True, "c": False},
            new_part_key="A",
            existing_part_keys=["x", "y", "z", "a", "b", "c"],
            expected_value={"A": f"list(0.5,c(1.0),{NULL},123,{TRUE},{FALSE})"},
        ),
    ],
)
def test__number_list_from_parts__returns_expected_serialized_list(
    data: FromPartsTestData,
):
    number_from_parts(
        data.parts, data.new_part_key, data.existing_part_keys, composite_type=List
    )
    assert data.parts == data.expected_value


@pytest.mark.parametrize(
    "data",
    [
        FromPartsTestData(
            parts={"a": "1", "b": "2"},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(c('1'),c('2'))"},
        ),
        FromPartsTestData(
            parts={"a": "1,2", "b": "3,4"},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(c('1','2'),c('3','4'))"},
        ),
        FromPartsTestData(
            parts={"a": "1", "b": "2", "c": "3"},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": "list(c('1'),c('2'))"},
        ),
        FromPartsTestData(
            parts={"a": "1", "b": "2"},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "list(c('1'),c('2'))"},
        ),
        FromPartsTestData(
            parts={"a": "1", "b": "2", "c": "3"},
            new_part_key="a",
            existing_part_keys=["a", "b"],
            expected_value={"a": "list(c('1'),c('2'))", "c": "3"},
        ),
        FromPartsTestData(
            parts={1: "1", 2: "2"},
            new_part_key=3,
            existing_part_keys=[1, 2],
            expected_value={3: "list(c('1'),c('2'))"},
        ),
        FromPartsTestData(
            parts={"a": None, "b": None},
            new_part_key="c",
            existing_part_keys=["a", "b"],
            expected_value={"c": NULL},
        ),
        FromPartsTestData(
            parts={
                "x": "0.5",
                "y": "1.0",
                "z": None,
                "a": "123",
                "b": "True",
                "c": "False",
            },
            new_part_key="A",
            existing_part_keys=["x", "y", "z", "a", "b", "c"],
            expected_value={
                "A": f"list(c('0.5'),c('1.0'),{NULL},c('123'),c('True'),c('False'))"
            },
        ),
    ],
)
def test__string_list_from_parts__returns_expected_serialized_list(
    data: FromPartsTestData,
):
    string_from_parts(
        data.parts, data.new_part_key, data.existing_part_keys, composite_type=List
    )
    assert data.parts == data.expected_value
