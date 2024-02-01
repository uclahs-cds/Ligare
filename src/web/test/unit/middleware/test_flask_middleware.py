import uuid
from typing import Callable, Literal
from uuid import uuid4

import pytest
from BL_Python.web.config import Config
from BL_Python.web.middleware import bind_errorhandler
from BL_Python.web.middleware.consts import CORRELATION_ID_HEADER
from BL_Python.web.middleware.flask import (
    _get_correlation_id,  # pyright: ignore[reportPrivateUsage]
)
from BL_Python.web.middleware.flask import bind_requesthandler
from flask import Flask, Response, abort
from mock import MagicMock
from pytest_mock import MockerFixture
from werkzeug.exceptions import BadRequest, HTTPException, Unauthorized

from ..create_app import (
    CreateApp,
    FlaskClientInjector,
    FlaskClientInjectorConfigurable,
    RequestConfigurable,
)


class TestFlaskMiddleware(CreateApp):
    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___register_api_response_handlers__sets_correlation_id_response_header_when_not_set_in_request_header(
        self,
        format: Literal["plaintext", "JSON"],
        flask_client_configurable: FlaskClientInjectorConfigurable,
        basic_config: Config,
    ):
        basic_config.logging.format = format
        flask_client = flask_client_configurable(basic_config)
        response = flask_client.client.get("/")

        assert response.headers[CORRELATION_ID_HEADER]
        _ = uuid.UUID(response.headers[CORRELATION_ID_HEADER])

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___register_api_response_handlers__sets_correlation_id_response_header_when_set_in_request_header(
        self,
        format: Literal["plaintext", "JSON"],
        flask_client_configurable: FlaskClientInjectorConfigurable,
        basic_config: Config,
    ):
        basic_config.logging.format = format
        flask_client = flask_client_configurable(basic_config)
        correlation_id = str(uuid4())
        response = flask_client.client.get(
            "/", headers={CORRELATION_ID_HEADER: correlation_id}
        )

        assert response.headers[CORRELATION_ID_HEADER] == correlation_id

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__validates_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        flask_request_configurable: RequestConfigurable,
        basic_config: Config,
    ):
        basic_config.logging.format = format
        correlation_id = "abc123"
        with flask_request_configurable(
            basic_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
        ):
            with pytest.raises(
                ValueError, match="^badly formed hexadecimal UUID string$"
            ):
                _ = _get_correlation_id(MagicMock())

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__uses_existing_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        flask_request_configurable: RequestConfigurable,
        basic_config: Config,
    ):
        basic_config.logging.format = format
        correlation_id = str(uuid4())
        with flask_request_configurable(
            basic_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
        ):
            returned_correlation_id = _get_correlation_id(MagicMock())
            assert correlation_id == returned_correlation_id

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__sets_correlation_id(
        self,
        format: Literal["plaintext", "JSON"],
        flask_request_configurable: RequestConfigurable,
        basic_config: Config,
    ):
        basic_config.logging.format = format
        with flask_request_configurable(basic_config):
            correlation_id = _get_correlation_id(MagicMock())

            assert correlation_id
            _ = uuid.UUID(correlation_id)

    def test__bind_requesthandler__returns_decorated_flask_request_hook(
        self,
        flask_client: FlaskClientInjector,
    ):
        flask_request_hook_mock = MagicMock()

        wrapped_decorator = bind_requesthandler(
            flask_client.client.application, flask_request_hook_mock
        )
        _ = wrapped_decorator(lambda: None)

        assert flask_request_hook_mock.called

    def test__bind_requesthandler__calls_decorated_function_when_app_is_run(
        self,
        flask_client: FlaskClientInjector,
    ):
        wrapped_handler_decorator = bind_requesthandler(
            flask_client.client.application, Flask.before_request
        )
        request_handler_mock = MagicMock()
        _ = wrapped_handler_decorator(request_handler_mock)

        _ = flask_client.client.get("/")

        assert request_handler_mock.called

    @pytest.mark.parametrize("code_or_exception", [Exception, HTTPException, 401])
    def test__bind_errorhandler__binds_flask_errorhandler(
        self,
        code_or_exception: type[Exception] | int,
        flask_client: FlaskClientInjector,
        mocker: MockerFixture,
    ):
        flask_errorhandler_mock = mocker.patch("flask.Flask.errorhandler")

        _ = bind_errorhandler(flask_client.client.application, code_or_exception)

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
    ):
        application_errorhandler_mock = MagicMock()
        with Flask("foo").test_client() as test_client:
            _ = bind_errorhandler(test_client.application, code_or_exception_type)(
                application_errorhandler_mock
            )
            # this probably doesn't need to be done w/ connexion
            _ = test_client.application.route("/")(failure_lambda)

            _ = test_client.get("/")

        assert application_errorhandler_mock.called
        assert isinstance(
            application_errorhandler_mock.call_args[0][0], expected_exception_type
        )
