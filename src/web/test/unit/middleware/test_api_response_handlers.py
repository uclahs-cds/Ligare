import logging
from test.unit.create_app import CreateApp
from typing import Any, cast

import pytest
from BL_Python.web.middleware import (
    CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER,
    OUTGOING_RESPONSE_MESSAGE,
    bind_requesthandler,
    register_api_request_handlers,
)
from flask import Flask, Response
from flask.testing import FlaskClient
from flask_injector import FlaskInjector
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture


class TestApiResponseHandlers(CreateApp):
    def test__register_api_response_handlers__binds_flask_before_request(
        self, flask_client: FlaskClient, mocker: MockerFixture
    ):
        flask_before_request_mock = mocker.patch(
            "flask.sansio.scaffold.Scaffold.before_request"
        )

        register_api_request_handlers(flask_client.application)

        assert flask_before_request_mock.called

    @pytest.mark.parametrize(
        "header,value",
        [
            (CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER, "example.com"),
            (CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER, ""),
            (CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER, ""),
        ],
    )
    def test__wrap_all_api_responses__sets_CORS_headers(
        self, header: str, value: str, flask_client: FlaskClient, mocker: MockerFixture
    ):
        config = self._get_basic_config()
        config.web.security.cors.origin = value
        _ = mocker.patch("BL_Python.web.middleware.Config", side_effect=config)
        _ = flask_client.get("/")

    def test__log_all_api_responses__logs_response_information(
        self,
        flask_client: FlaskClient,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.get("/")

        msg = OUTGOING_RESPONSE_MESSAGE % (
            response.status_code,
            response.status,
        )

        assert msg in {record.message for record in caplog.records}

    @pytest.mark.parametrize("property_name", ["correlation_id", "headers"])
    def test__log_all_api_responses__logs_extra_response_information(
        self,
        property_name: str,
        flask_client: FlaskClient,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.get("/")

        msg = OUTGOING_RESPONSE_MESSAGE % (
            response.status_code,
            response.status,
        )

        records = [
            cast(dict[str, Any], cast(Any, record).props)
            for record in caplog.records
            if record.message == msg
        ]
        for record_props in records:
            assert property_name in record_props
            assert record_props[property_name]

    def test__log_all_api_responses__logs_response_headers_without_session_id(
        self,
        flask_client: FlaskClient,
        caplog: LogCaptureFixture,
    ):
        wrapped_handler_decorator = bind_requesthandler(
            flask_client.application, Flask.before_request
        )

        def set_session_cookie():
            response = cast(
                FlaskInjector,
                flask_client.application.injector,  # pyright: ignore[reportUnknownMemberType,reportGeneralTypeIssues]
            ).injector.get(Response)
            response.set_cookie("session", "foo")
            return response

        _ = wrapped_handler_decorator(set_session_cookie)

        with caplog.at_level(logging.DEBUG):
            response = flask_client.get("/")
        msg = OUTGOING_RESPONSE_MESSAGE % (
            response.status_code,
            response.status,
        )

        records = [
            cast(dict[str, Any], cast(Any, record).props)
            for record in caplog.records
            if record.message == msg
        ]
        for record_props in records:
            assert "headers" in record_props
            assert "Set-Cookie" in record_props["headers"]
            assert "session=<redacted>" in record_props["headers"]["Set-Cookie"]
