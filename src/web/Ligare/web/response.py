import json
from dataclasses import dataclass
from enum import Enum

from flask import Response


class OutputType(Enum):
    PNG = "png"
    TIFF = "tiff"


@dataclass
class ErrorDetail:
    source: str


def create_attachment_response(
    data: bytes,
    attachment_filename: str = "download",
    output_type: OutputType = OutputType.PNG,
) -> Response:
    """
    Create a new `Response` with appropriate headers for sending
    PNG data. The response body is the PNG data.

    :param bytes data: The PNG data.
    :param str attachment_filename: The name of the filename in the
      `Content-Disposition` response header, defaults to "download".
    :return Response: The PNG HTTP response.
    """
    resp = Response(data)
    resp.headers["Content-Disposition"] = (
        f"attachment; filename={attachment_filename}.{output_type.value}"
    )
    resp.headers["Content-Type"] = f"image/{output_type.value}"
    return resp


def create_BadRequest_response(
    error_msg: str, details: list[ErrorDetail] | None = None
) -> Response:
    """
    Create a 400 `Response.

    :param str error_msg: An error message to include in the response's JSON data.
    :return Response: A 400 Bed Request HTTP response. The response body is
      a JSON object with the following structure:
      {
        "error_msg": error_msg,
        "status": "Bad Request",
        "status_code": 400,
        "details": [...]
      }
    """
    resp = Response(
        json.dumps({
            "error_msg": error_msg,
            "status": "Bad Request",
            "status_code": 400,
            "details": [vars(detail) for detail in details] if details else [],
        }),
        400,
        content_type="application/json",
    )

    return resp
