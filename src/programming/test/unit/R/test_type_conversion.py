from dataclasses import dataclass
from typing import Any

import pytest
from Ligare.programming.R.type_conversion import (
    NULL,
    Boolean,
    Composite,
    List,
    Number,
    Seq,
    SerializedType,
    String,
    Vector,
    boolean,
    number,
    string,
)


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
    assert result.serialize() == expected_value


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
    result = string(input_value, comma_separated=True).serialize()
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
    assert result.serialize() == expected_value


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
    result = number(input_value, comma_separated=True).serialize()
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
    result = string(input_value, vector=True).serialize()
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
    result = boolean(input_value).serialize()
    assert result == expected_value


@dataclass
class FromPartsTestData:
    parts: dict[Any, Any]
    new_part_key: Any
    existing_part_keys: list[Any]
    expected_value: dict[Any, Any]


@pytest.mark.parametrize(
    "input,expected",
    (
        [1, "1"],
        [123, "123"],
        [-123, "-123"],
        [0.1, "0.1"],
        [None, NULL],
        [0, "0"],
        ["123", "123"],
    ),
)
def test__Number__serializes_numeric_values(
    input: int | float | str | None, expected: str | None
):
    number = Number(input)
    assert number.serialize() == expected


@pytest.mark.parametrize(
    "input,expected",
    (
        ["1", "'1'"],
        [1, "'1'"],
        [0.1, "'0.1'"],
        [-1, "'-1'"],
        ["abc", "'abc'"],
        [None, NULL],
    ),
)
def test__String__serializes_string_values(
    input: int | float | str | None, expected: str | None
):
    string = String(input)
    assert string.serialize() == expected


@pytest.mark.parametrize(
    "composite_type,composite_type_keyword,input,expected",
    (
        [Vector, "c", [String("1")], "('1')"],
        [Vector, "c", [String("1"), String("2")], "('1','2')"],
        [Vector, "c", [String("a"), String("b")], "('a','b')"],
        [Vector, "c", [String(None), None], f"({NULL},{NULL})"],
        [Vector, "c", [Number("1")], "(1)"],
        [Vector, "c", [Number("1"), Number("2")], "(1,2)"],
        [Vector, "c", [Number(None), None], f"({NULL},{NULL})"],
        [Vector, "c", [String("1"), Number("1")], "('1',1)"],
        [
            Vector,
            "c",
            [String("1"), Number("1"), String("2"), Number("2")],
            "('1',1,'2',2)",
        ],
        [
            Vector,
            "c",
            [String("a"), Number("1"), String("b"), Number("2")],
            "('a',1,'b',2)",
        ],
        [Vector, "c", [String(None), Number(None), None], f"({NULL},{NULL},{NULL})"],
        [Vector, "c", [None], f"({NULL})"],
        [Vector, "c", [None, None], f"({NULL},{NULL})"],
        [List, "list", [String("1")], "('1')"],
        [List, "list", [String("1"), String("2")], "('1','2')"],
        [List, "list", [String("a"), String("b")], "('a','b')"],
        [List, "list", [String(None), None], f"({NULL},{NULL})"],
        [List, "list", [Number("1")], "(1)"],
        [List, "list", [Number("1"), Number("2")], "(1,2)"],
        [List, "list", [Number(None), None], f"({NULL},{NULL})"],
        [List, "list", [String("1"), Number("1")], "('1',1)"],
        [
            List,
            "list",
            [String("1"), Number("1"), String("2"), Number("2")],
            "('1',1,'2',2)",
        ],
        [
            List,
            "list",
            [String("a"), Number("1"), String("b"), Number("2")],
            "('a',1,'b',2)",
        ],
        [List, "list", [String(None), Number(None), None], f"({NULL},{NULL},{NULL})"],
        [List, "list", [None], f"({NULL})"],
        [List, "list", [None, None], f"({NULL},{NULL})"],
        [Seq, "seq", [String("1")], "('1')"],
        [Seq, "seq", [String("1"), String("2")], "('1','2')"],
        [Seq, "seq", [String("a"), String("b")], "('a','b')"],
        [Seq, "seq", [String(None), None], f"({NULL},{NULL})"],
        [Seq, "seq", [Number("1")], "(1)"],
        [Seq, "seq", [Number("1"), Number("2")], "(1,2)"],
        [Seq, "seq", [Number(None), None], f"({NULL},{NULL})"],
        [Seq, "seq", [String("1"), Number("1")], "('1',1)"],
        [
            Seq,
            "seq",
            [String("1"), Number("1"), String("2"), Number("2")],
            "('1',1,'2',2)",
        ],
        [
            Seq,
            "seq",
            [String("a"), Number("1"), String("b"), Number("2")],
            "('a',1,'b',2)",
        ],
        [Seq, "seq", [String(None), Number(None), None], f"({NULL},{NULL},{NULL})"],
        [Seq, "seq", [None], f"({NULL})"],
        [Seq, "seq", [None, None], f"({NULL},{NULL})"],
    ),
)
def test__Composite__serializes_serializable_types(
    composite_type: type[Composite],
    composite_type_keyword: str,
    input: Any,
    expected: Any,
):
    vector = composite_type(input)
    assert vector.serialize() == f"{composite_type_keyword}{expected}"


@pytest.mark.parametrize(
    "composite_type,composite_type_keyword,input,expected",
    (
        [Vector, "c", [Vector([String("1")])], "(c('1'))"],
        [Vector, "c", [Vector([String("1"), String("2")])], "(c('1','2'))"],
        [Vector, "c", [Vector([String("a"), String("b")])], "(c('a','b'))"],
        [Vector, "c", [Vector([String(None), None])], f"(c({NULL},{NULL}))"],
        [Vector, "c", [Vector([Number("1")])], "(c(1))"],
        [Vector, "c", [Vector([Number("1"), Number("2")])], "(c(1,2))"],
        [Vector, "c", [Vector([Number(None), None])], f"(c({NULL},{NULL}))"],
        [Vector, "c", [Vector([String("1"), Number("1")])], "(c('1',1))"],
        [
            Vector,
            "c",
            [Vector([String("1"), Number("1"), String("2"), Number("2")])],
            "(c('1',1,'2',2))",
        ],
        [
            Vector,
            "c",
            [Vector([String("a"), Number("1"), String("b"), Number("2")])],
            "(c('a',1,'b',2))",
        ],
        [
            Vector,
            "c",
            [Vector([String(None), Number(None), None])],
            f"(c({NULL},{NULL},{NULL}))",
        ],
        [Vector, "c", [Vector([None])], f"(c({NULL}))"],
        [Vector, "c", [Vector([None, None])], f"(c({NULL},{NULL}))"],
        [
            List,
            "list",
            [List([String("a"), Number("1"), String("b"), Number("2")])],
            "(list('a',1,'b',2))",
        ],
        [
            Seq,
            "seq",
            [Seq([String("a"), Number("1"), String("b"), Number("2")])],
            "(seq('a',1,'b',2))",
        ],
        [
            List,
            "list",
            [
                List([
                    String("a"),
                    Number("1"),
                    Vector([
                        String("b"),
                        Number("2"),
                        Seq([String("a"), None, Number("2")]),
                    ]),
                ])
            ],
            f"(list('a',1,c('b',2,seq('a',{NULL},2))))",
        ],
    ),
)
def test__Composite__serializes_composite_types(
    composite_type: type[Composite],
    composite_type_keyword: str,
    input: Any,
    expected: Any,
):
    vector = composite_type(input)
    assert vector.serialize() == f"{composite_type_keyword}{expected}"


@pytest.mark.parametrize("composite_type", (Composite, Vector, List, Seq))
def test__Composite__serializes_None(composite_type: type[Composite]):
    result = composite_type(None).serialize()
    assert result == NULL


@pytest.mark.parametrize(
    "value",
    (
        None,
        String("abc"),
        String("a,b,c"),
        Number(123),
        String("None,None"),
        Boolean(False),
        Boolean(True),
        Number(0),
    ),
)
def test__Composite__generic_type_returns_noncomposite_value(
    value: SerializedType | None,
):
    result = Composite([value]).serialize()
    if value is None:
        assert result is NULL
    else:
        assert result == value.serialize()
