import logging
from typing import Any, cast

import pytest
from BL_Python.web.middleware import register_api_request_handlers
from BL_Python.web.middleware.consts import INCOMING_REQUEST_MESSAGE
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture

from ..create_app import CreateApp, FlaskClientInjector


class TestApiRequestHandlers(CreateApp):
    def test__register_api_request_handlers__binds_flask_before_request(
        self, flask_client: FlaskClientInjector, mocker: MockerFixture
    ):
        flask_before_request_mock = mocker.patch(
            "flask.sansio.scaffold.Scaffold.before_request"
        )

        _ = register_api_request_handlers(flask_client.client.application)

        assert flask_before_request_mock.called

    def test__log_all_api_requests__logs_request_information(
        self,
        flask_client: FlaskClientInjector,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.client.get("/")

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
        flask_client: FlaskClientInjector,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.client.get("/")

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
        flask_client: FlaskClientInjector,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.client.get("/")

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
