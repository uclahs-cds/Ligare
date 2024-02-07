import logging
from typing import Any, cast

import pytest
from BL_Python.web.config import Config
from BL_Python.web.middleware import register_api_request_handlers
from BL_Python.web.middleware.consts import (
    CONTENT_SECURITY_POLICY_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER,
    CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER,
    OUTGOING_RESPONSE_MESSAGE,
)
from BL_Python.web.middleware.flask import bind_requesthandler
from flask import Flask, Response
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture

from ..create_app import CreateApp, FlaskClientInjector, FlaskClientInjectorConfigurable


class TestApiResponseHandlers(CreateApp):
    def test__register_api_response_handlers__binds_flask_before_request(
        self, flask_client: FlaskClientInjector, mocker: MockerFixture
    ):
        flask_before_request_mock = mocker.patch(
            "flask.sansio.scaffold.Scaffold.before_request"
        )

        _ = register_api_request_handlers(flask_client.client.application)

        assert flask_before_request_mock.called

    def test__wrap_all_api_responses__sets_CSP_header(
        self,
        flask_client_configurable: FlaskClientInjectorConfigurable,
        basic_config: Config,
    ):
        csp_value = "default-src 'self' cdn.example.com;"
        basic_config.web.security.csp = csp_value
        flask_client = flask_client_configurable(basic_config)
        response = flask_client.client.get("/")
        header_value = response.headers.get(CONTENT_SECURITY_POLICY_HEADER)
        assert header_value == csp_value

    @pytest.mark.parametrize(
        "header,value,config_attribute_name",
        [
            (CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER, "example.com", "origin"),
            (
                CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER,
                "False",
                "allow_credentials",
            ),
            (
                CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER,
                "True",
                "allow_credentials",
            ),
            (CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER, ["GET"], "allow_methods"),
            (
                CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER,
                ["POST", "OPTIONS", "GET"],
                "allow_methods",
            ),
        ],
    )
    def test__wrap_all_api_responses__sets_CORS_headers(
        self,
        header: str,
        value: str,
        config_attribute_name: str,
        flask_client_configurable: FlaskClientInjectorConfigurable,
        basic_config: Config,
    ):
        setattr(basic_config.web.security.cors, config_attribute_name, value)
        flask_client = flask_client_configurable(basic_config)
        response = flask_client.client.get("/")
        header_value = response.headers.get(header)
        assert header_value == ",".join(value) if isinstance(value, list) else value

    def test__log_all_api_responses__logs_response_information(
        self,
        flask_client: FlaskClientInjector,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.client.get("/")

        msg = OUTGOING_RESPONSE_MESSAGE % (
            response.status_code,
            response.status,
        )

        assert msg in {record.message for record in caplog.records}

    @pytest.mark.parametrize("property_name", ["correlation_id", "headers"])
    def test__log_all_api_responses__logs_extra_response_information(
        self,
        property_name: str,
        flask_client: FlaskClientInjector,
        caplog: LogCaptureFixture,
    ):
        with caplog.at_level(logging.DEBUG):
            response = flask_client.client.get("/")

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
        flask_client: FlaskClientInjector,
        caplog: LogCaptureFixture,
    ):
        wrapped_handler_decorator = bind_requesthandler(
            flask_client.client.application, Flask.before_request
        )

        def set_session_cookie():
            response = flask_client.injector.injector.get(Response)
            response.set_cookie("session", "foo")
            return response

        _ = wrapped_handler_decorator(set_session_cookie)

        with caplog.at_level(logging.DEBUG):
            response = flask_client.client.get("/")
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
