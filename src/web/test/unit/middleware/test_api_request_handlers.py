import logging
from test.unit.create_app import CreateApp
from typing import Any, cast

import pytest
from BL_Python.web.middleware import (
    INCOMING_REQUEST_MESSAGE,
    bind_requesthandler,
    register_api_request_handlers,
)
from flask import Flask
from flask.testing import FlaskClient
from mock import MagicMock
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture


class TestApiRequestHandlers(CreateApp):
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

    def test__register_api_request_handlers__binds_flask_before_request(
        self, flask_client: FlaskClient, mocker: MockerFixture
    ):
        flask_before_request_mock = mocker.patch(
            "flask.sansio.scaffold.Scaffold.before_request"
        )

        register_api_request_handlers(flask_client.application)

        assert flask_before_request_mock.called

    def test__log_all_api_requests__logs_request_information(
        self,
        flask_client: FlaskClient,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.get("/")

        request = response.request
        msg = INCOMING_REQUEST_MESSAGE % (
            request.method,
            request.url,
            request.host,
            request.remote_addr,
            request.remote_user,
        )

        assert msg in {record.message for record in caplog.records}

    @pytest.mark.parametrize("property_name", ["correlation_id", "headers"])
    def test__log_all_api_requests__logs_extra_request_information(
        self,
        property_name: str,
        flask_client: FlaskClient,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.get("/")

        request = response.request
        msg = INCOMING_REQUEST_MESSAGE % (
            request.method,
            request.url,
            request.host,
            request.remote_addr,
            request.remote_user,
        )

        records = [
            cast(dict[str, Any], cast(Any, record).props)
            for record in caplog.records
            if record.message == msg
        ]
        for record_props in records:
            assert property_name in record_props
            assert record_props[property_name]

    def test__log_all_api_requests__logs_request_headers_without_session_id(
        self,
        flask_client: FlaskClient,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.get("/")

        request = response.request
        msg = INCOMING_REQUEST_MESSAGE % (
            request.method,
            request.url,
            request.host,
            request.remote_addr,
            request.remote_user,
        )

        records = [
            cast(dict[str, Any], cast(Any, record).props)
            for record in caplog.records
            if record.message == msg
        ]
        for record_props in records:
            assert "headers" in record_props
            assert "Cookie" in record_props["headers"]
            assert "session=<redacted>" in record_props["headers"]["Cookie"]
