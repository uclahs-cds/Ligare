from typing import Callable

import pytest
from BL_Python.web.middleware import (
    _get_correlation_id,  # pyright: ignore[reportPrivateUsage,reportUnusedImport]
)
from BL_Python.web.middleware import (
    CORRELATION_ID_HEADER,
    bind_errorhandler,
    bind_requesthandler,
)
from flask import Flask, Response, abort, session  # pyright: ignore[reportUnusedImport]
from flask.ctx import RequestContext
from flask.testing import FlaskClient
from mock import MagicMock
from pytest_mock import MockerFixture
from werkzeug.exceptions import BadRequest, HTTPException, Unauthorized

from ..create_app import CreateApp


class TestMiddleware(CreateApp):
    def test___get_correlation_id__uses_existing_correlation_id_when_already_set(self):
        pass

    def test___get_correlation_id__sets_correlation_id_when_json_logging_enabled(self):
        pass

    def test___get_correlation_id__sets_correlation_id_when_json_logging_disabled(
        self, flask_request: RequestContext, mocker: MockerFixture
    ):
        ## m = mocker.patch("BL_Python.web.middleware.session")
        # mocker.patch.object(flask_request.session, "__getitem__", return_value=a)
        # mocker.patch.object(flask_request.session, "get", return_value=b)
        # mocker.patch.object(session, "__setitem__")
        correlation_id = _get_correlation_id(MagicMock())
        assert session[CORRELATION_ID_HEADER] == correlation_id

    def test__bind_requesthandler__returns_decorated_flask_request_hook(
        self, flask_client: FlaskClient
    ):
        flask_request_hook_mock = MagicMock()

        wrapped_decorator = bind_requesthandler(
            flask_client.application, flask_request_hook_mock
        )
        _ = wrapped_decorator(lambda: None)

        assert flask_request_hook_mock.called

    def test__bind_requesthandler__calls_decorated_function_when_app_is_run(
        self, flask_client: FlaskClient
    ):
        wrapped_handler_decorator = bind_requesthandler(
            flask_client.application, Flask.before_request
        )
        request_handler_mock = MagicMock()
        _ = wrapped_handler_decorator(request_handler_mock)

        _ = flask_client.get("/")

        assert request_handler_mock.called

    @pytest.mark.parametrize("code_or_exception", [Exception, HTTPException, 401])
    def test__bind_errorhandler__binds_flask_errorhandler(
        self,
        code_or_exception: type[Exception] | int,
        flask_client: FlaskClient,
        mocker: MockerFixture,
    ):
        flask_errorhandler_mock = mocker.patch("flask.Flask.errorhandler")

        _ = bind_errorhandler(flask_client.application, code_or_exception)

        flask_errorhandler_mock.assert_called_with(code_or_exception)

    @pytest.mark.parametrize(
        "code_or_exception_type,expected_exception_type,failure_lambda",
        [
            (
                Exception,
                ZeroDivisionError,
                lambda: 1 / 0,  # 1/0 to raise an exception (any exception)
            ),
            (HTTPException, BadRequest, lambda: abort(400)),
            (401, Unauthorized, lambda: abort(401)),
        ],
    )
    def test__bind_errorhandler__calls_decorated_function_with_correct_error_when_error_occurs_during_request(
        self,
        code_or_exception_type: type[Exception] | int,
        expected_exception_type: type[Exception],
        failure_lambda: Callable[[], Response],
        flask_client: FlaskClient,
    ):
        application_errorhandler_mock = MagicMock()
        _ = bind_errorhandler(flask_client.application, code_or_exception_type)(
            application_errorhandler_mock
        )
        _ = flask_client.application.route("/")(failure_lambda)

        _ = flask_client.get("/")

        assert application_errorhandler_mock.called
        assert isinstance(
            application_errorhandler_mock.call_args[0][0], expected_exception_type
        )
