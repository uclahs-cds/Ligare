from json.decoder import JSONDecoder
from typing import Callable

import pytest
from flask import Response, abort
from werkzeug.exceptions import Unauthorized

from ..create_app import CreateApp, FlaskClientInjector


def _raise_custom_unauthorized_exception():
    response = Response("Unauthorized.", 401)
    raise Unauthorized(response.data, response)


class TestErrorHandlers(CreateApp):
    @pytest.mark.parametrize(
        "expected_status_code,expected_status_msg,failure_lambda",
        [
            (
                500,
                "Internal Server Error",
                lambda: 1 / 0,  # 1/0 to raise an exception (any exception)
            ),
            (400, "Bad Request", lambda: abort(400)),
            (401, "Unauthorized", lambda: abort(401)),
            (401, "401 UNAUTHORIZED", _raise_custom_unauthorized_exception),
        ],
    )
    def test__bind_errorhandler__calls_decorated_function_with_correct_error_when_error_occurs_during_request(
        self,
        expected_status_code: int,
        expected_status_msg: str,
        failure_lambda: Callable[[], Response],
        flask_client: FlaskClientInjector,
    ):
        _ = flask_client.client.application.route("/")(failure_lambda)

        response = flask_client.client.get("/")
        response_dict: dict[str, str | int] = JSONDecoder().decode(response.text)

        assert response_dict["error_msg"]
        assert response_dict["status_code"] == expected_status_code
        assert response_dict["status"] == expected_status_msg
