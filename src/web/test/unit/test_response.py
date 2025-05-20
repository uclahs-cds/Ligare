from typing import Any

import pytest
from Ligare.web.response import (
    ErrorDetail,
    OutputType,
    create_attachment_response,
    create_BadRequest_response,
)


def test__create_BadRequest_response__sets_content_type_correctly():
    response = create_BadRequest_response("foo")
    assert response.content_type == "application/json"


def test__create_BadRequest_response__sets_error_msg_correctly():
    response = create_BadRequest_response("foo")
    assert response.json is not None
    assert response.json.get("error_msg") == "foo"


def test__create_BadRequest_response__sets_status_correctly():
    response = create_BadRequest_response("foo")
    assert response.json is not None
    assert response.json.get("status") == "Bad Request"
    assert response.json.get("status_code") == 400
    assert response.status_code == 400


def test__create_BadRequest_response__sets_details_correctly_when_none():
    response = create_BadRequest_response("foo")
    assert response.json is not None
    assert response.json.get("details") == []


@pytest.mark.parametrize(
    "input,expected",
    [
        ([], []),
        ([ErrorDetail("test")], [{"source": "test"}]),
    ],
)
def test__create_BadRequest_response__sets_details_correctly(input: Any, expected: Any):
    response = create_BadRequest_response("foo", input)
    assert response.json is not None
    assert response.json.get("details") == expected


@pytest.mark.parametrize(
    "attachment_filename,output_type",
    [
        ([None, None]),
        (["foo", OutputType.PNG]),
        (["bar", OutputType.TIFF]),
    ],
)
def test__create_attachment_response__sets_headers_correctly(
    attachment_filename: str | None, output_type: OutputType | None
):
    if attachment_filename is None or output_type is None:
        response = create_attachment_response(b"")
        # use defaults
        attachment_filename = "download"
        output_type = OutputType.PNG
    else:
        response = create_attachment_response(b"", attachment_filename, output_type)

    assert (
        response.headers.get("Content-Disposition")
        == f"attachment; filename={attachment_filename}.{output_type.value}"
    )
    assert response.headers.get("Content-Type") == f"image/{output_type.value}"


def test__create_attachment_response__sets_data_correctly():
    response = create_attachment_response(b"foo")
    assert response.data == b"foo"
