import uuid
from typing import Literal

import pytest
from BL_Python.web.application import AppInjector, FlaskAppInjector, OpenAPIAppInjector
from BL_Python.web.config import Config
from BL_Python.web.middleware import (
    CORRELATION_ID_HEADER,
    _get_correlation_id,
    bind_errorhandler,
    bind_requesthandler,
)
from connexion import FlaskApp
from flask import Flask, abort
from mock import MagicMock
from pytest_mock import MockerFixture
from werkzeug.exceptions import BadRequest, HTTPException, Unauthorized

from ..create_app import (
    CreateApp,
    OpenAPIClientInjector,
    OpenAPIClientInjectorConfigurable,
    OpenAPIMockController,
    RequestConfigurable,
)


##
##
## class TestMiddleware(CreateApp):
##    @pytest.mark.parametrize(
##        "config_type,format",
##        [
##            ("basic", ["plaintext", "JSON"]),
##            ("openapi", ["plaintext", "JSON"]),
##        ],
##    )
##    def test___register_api_response_handlers__sets_correlation_id_response_header_when_not_set_in_request_header(
##        self,
##        config_type: str,
##        format: Literal["plaintext", "JSON"],
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##        openapi_config: Config,
##    ):
##        openapi_config.logging.format = format
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##        flask_client = openapi_client_configurable(openapi_config)
##        response = flask_client.client.get("/")
##
##        assert response.headers[CORRELATION_ID_HEADER]
##        _ = uuid.UUID(response.headers[CORRELATION_ID_HEADER])
##
##    @pytest.mark.parametrize(
##        "config_type,format",
##        [
##            ("basic", ["plaintext", "JSON"]),
##            ("openapi", ["plaintext", "JSON"]),
##        ],
##    )
##    def test___register_api_response_handlers__sets_correlation_id_response_header_when_set_in_request_header(
##        self,
##        config_type: str,
##        format: Literal["plaintext", "JSON"],
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##        openapi_config: Config,
##    ):
##        openapi_config.logging.format = format
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##        flask_client = openapi_client_configurable(openapi_config)
##        correlation_id = str(uuid4())
##        response = flask_client.client.get(
##            "/", headers={CORRELATION_ID_HEADER: correlation_id}
##        )
##
##        assert response.headers[CORRELATION_ID_HEADER] == correlation_id
##
##    @pytest.mark.parametrize(
##        "config_type,format",
##        [
##            ("basic", ["plaintext", "JSON"]),
##            ("openapi", ["plaintext", "JSON"]),
##        ],
##    )
##    def test___get_correlation_id__validates_correlation_id_when_set_in_request_headers(
##        self,
##        config_type: str,
##        format: Literal["plaintext", "JSON"],
##        flask_request_configurable: RequestConfigurable,
##        openapi_config: Config,
##    ):
##        openapi_config.logging.format = format
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##        correlation_id = "abc123"
##        with flask_request_configurable(
##            openapi_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
##        ):
##            with pytest.raises(
##                ValueError, match="^badly formed hexadecimal UUID string$"
##            ):
##                _ = _get_correlation_id(MagicMock())
##
##    @pytest.mark.parametrize(
##        "config_type,format",
##        [
##            ("basic", ["plaintext", "JSON"]),
##            ("openapi", ["plaintext", "JSON"]),
##        ],
##    )
##    def test___get_correlation_id__uses_existing_correlation_id_when_set_in_request_headers(
##        self,
##        config_type: str,
##        format: Literal["plaintext", "JSON"],
##        flask_request_configurable: RequestConfigurable,
##        openapi_config: Config,
##    ):
##        openapi_config.logging.format = format
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##        correlation_id = str(uuid4())
##        with flask_request_configurable(
##            openapi_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
##        ):
##            correlation_id = _get_correlation_id(MagicMock())
##            assert correlation_id == correlation_id
##
##    @pytest.mark.parametrize(
##        "config_type,format",
##        [
##            ("basic", ["plaintext", "JSON"]),
##            ("openapi", ["plaintext", "JSON"]),
##        ],
##    )
##    def test___get_correlation_id__sets_correlation_id(
##        self,
##        config_type: str,
##        format: Literal["plaintext", "JSON"],
##        flask_request_configurable: RequestConfigurable,
##        openapi_config: Config,
##    ):
##        openapi_config.logging.format = format
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##        with flask_request_configurable(openapi_config):
##            correlation_id = _get_correlation_id(MagicMock())
##
##            assert correlation_id
##            _ = uuid.UUID(correlation_id)
##
##    @pytest.mark.parametrize("config_type", ["basic", "openapi"])
##    def test__bind_requesthandler__returns_decorated_flask_request_hook(
##        self,
##        config_type: str,
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##        openapi_config: Config,
##    ):
##        flask_request_hook_mock = MagicMock()
##
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##
##        flask_client = openapi_client_configurable(openapi_config)
##        if isinstance(flask_client.client, FlaskClient):
##            wrapped_decorator = bind_requesthandler(
##                flask_client.client.application, flask_request_hook_mock
##            )
##        else:
##            wrapped_decorator = bind_requesthandler(
##                flask_client.client.app, flask_request_hook_mock
##            )
##        _ = wrapped_decorator(lambda: None)
##
##        assert flask_request_hook_mock.called
##
##    @pytest.mark.parametrize("config_type", ["basic"])  # , "openapi"])
##    def test__bind_requesthandler__calls_decorated_function_when_app_is_run(
##        self,
##        config_type: str,
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##        openapi_config: Config,
##    ):
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##
##        flask_client = openapi_client_configurable(openapi_config)
##        wrapped_handler_decorator = bind_requesthandler(
##            flask_client.client.application, Flask.before_request
##        )
##        request_handler_mock = MagicMock()
##        _ = wrapped_handler_decorator(request_handler_mock)
##
##        _ = flask_client.client.get("/")
##
##        assert request_handler_mock.called
##
##    @pytest.mark.parametrize(
##        "code_or_exception,config_type",
##        [
##            (Exception, "basic"),
##            (HTTPException, "basic"),
##            (401, "basic"),
##            (Exception, "openapi"),
##            (HTTPException, "openapi"),
##            (401, "openapi"),
##        ],
##    )
##    def test__bind_errorhandler__binds_flask_errorhandler(
##        self,
##        code_or_exception: type[Exception] | int,
##        config_type: str,
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##        openapi_config: Config,
##        mocker: MockerFixture,
##    ):
##        flask_errorhandler_mock = mocker.patch("flask.Flask.errorhandler")
##
##        if config_type == "openapi":
##            cast(FlaskConfig, openapi_config.flask).openapi = FlaskOpenApiConfig(
##                spec_path=".", use_swagger=False
##            )
##
##        flask_client = openapi_client_configurable(openapi_config)
##
##        _ = bind_errorhandler(flask_client.client.application, code_or_exception)
##
##        flask_errorhandler_mock.assert_called_with(code_or_exception)
##
##    @pytest.mark.parametrize(
##        "code_or_exception_type,expected_exception_type,failure_lambda",
##        [
##            (
##                Exception,
##                ZeroDivisionError,
##                lambda: 1 / 0,  # 1/0 to raise an exception (any exception)
##            ),
##            (HTTPException, BadRequest, lambda: abort(400)),
##            (401, Unauthorized, lambda: abort(401)),
##        ],
##    )
##    def test__bind_errorhandler__from_Flask_calls_decorated_function_with_correct_error_when_error_occurs_during_request(
##        self,
##        code_or_exception_type: type[Exception] | int,
##        expected_exception_type: type[Exception],
##        failure_lambda: Callable[[], Response],
##        openapi_config: Config,
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##    ):
##        flask_client = openapi_client_configurable(openapi_config)
##
##        application_errorhandler_mock = MagicMock()
##        _ = bind_errorhandler(flask_client.client.application, code_or_exception_type)(
##            application_errorhandler_mock
##        )
##        # this probably doesn't need to be done w/ connexion
##        _ = flask_client.client.application.route("/")(failure_lambda)
##
##        _ = flask_client.client.get("/")
##
##        assert application_errorhandler_mock.called
##        assert isinstance(
##            application_errorhandler_mock.call_args[0][0], expected_exception_type
##        )
##
##    @pytest.mark.parametrize(
##        "code_or_exception_type,expected_exception_type,failure_lambda",
##        [
##            (
##                Exception,
##                ZeroDivisionError,
##                lambda: 1 / 0,  # 1/0 to raise an exception (any exception)
##            ),
##            (HTTPException, BadRequest, lambda: abort(400)),
##            (401, Unauthorized, lambda: abort(401)),
##        ],
##    )
##    def test__bind_errorhandler__from_Connexion_calls_decorated_function_with_correct_error_when_error_occurs_during_request(
##        self,
##        code_or_exception_type: type[Exception] | int,
##        expected_exception_type: type[Exception],
##        failure_lambda: Callable[[], Response],
##        openapi_config: Config,
##        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
##        mocker: MockerFixture,
##    ):
##        # fake_config_dict: AnyDict = {
##        #    "flask": {"app_name": "test_app", "session": {"cookie": {}}}
##        # }
##
##        # The resolver in Connexion uses importlib to find operations
##        # in the OpenAPI spec. Instead, just replace `import_module`
##        # with this method as the return value. Connexion also
##        # requires that the `root` attribute exists because that is
##        # the name of the OperationID in the fake OpenAPI spec.
##        def fake_operation_method():
##            return "Hello"
##
##        fake_operation_method.root = "/"
##
##        _ = mocker.patch(
##            "connexion.utils.importlib",
##            spec=importlib,
##            import_module=MagicMock(return_value=fake_operation_method),
##        )
##        _ = mocker.patch("io.open")
##        _ = mocker.patch(
##            "toml.decoder.loads",
##            return_value=toml.dumps(openapi_config.model_dump()),
##        )
##
##        application_errorhandler_mock = MagicMock()
##
##        def app_init_hook(app: FlaskAppInjector[FlaskApp]):
##            _ = bind_errorhandler(app.app, code_or_exception_type)(
##                application_errorhandler_mock
##            )
##            # _ = app.app.route("/")(failure_lambda)
##
##        flask_client = openapi_client_configurable(openapi_config, app_init_hook)
##
##        # this probably doesn't need to be done w/ connexion
##
##        _ = flask_client.client.get("/")
##
##        assert application_errorhandler_mock.called
##        assert isinstance(
##            application_errorhandler_mock.call_args[0][0], expected_exception_type
##        )
##
#
# import importlib
# import uuid
# from typing import Callable, Literal
# from uuid import uuid4
#
# import pytest
# import toml
# from BL_Python.web.application import AppInjector
# from BL_Python.web.config import Config
# from BL_Python.web.middleware import (
#    _get_correlation_id,  # pyright: ignore[reportPrivateUsage]
# )
# from BL_Python.web.middleware import (
#    CORRELATION_ID_HEADER,
#    bind_errorhandler,
#    bind_requesthandler,
# )
# from connexion.apps.flask import FlaskApp
# from flask import Flask, Response, abort
# from mock import MagicMock
# from pytest_mock import MockerFixture
# from werkzeug.exceptions import BadRequest, HTTPException, Unauthorized
#
# from ..create_app import (
#    CreateApp,
#    OpenAPIClientInjector,
#    OpenAPIClientInjectorConfigurable,
#    RequestConfigurable,
# )
#
#
# class TestOpenAPIMiddleware(CreateApp):
#    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
#    def test___register_api_response_handlers__sets_correlation_id_response_header_when_not_set_in_request_header(
#        self,
#        format: Literal["plaintext", "JSON"],
#        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
#        openapi_config: Config,
#        mocker: MockerFixture,
#    ):
#        ##openapi_config.logging.format = format
#        ##flask_client = openapi_client_configurable(openapi_config)
#        ##response = flask_client.client.get("/")
#        #########################################
#        # fake_config_dict: AnyDict = {
#        #    "flask": {"app_name": "test_app", "session": {"cookie": {}}}
#        # }
#
#        # The resolver in Connexion uses importlib to find operations
#        # in the OpenAPI spec. Instead, just replace `import_module`
#        # with this method as the return value. Connexion also
#        # requires that the `root` attribute exists because that is
#        # the name of the OperationID in the fake OpenAPI spec.
#        def fake_operation_method():
#            return "Hello"
#
#        fake_operation_method.root = "/"
#
#        _ = mocker.patch(
#            "connexion.utils.importlib",
#            spec=importlib,
#            import_module=MagicMock(return_value=fake_operation_method),
#        )
#        _ = mocker.patch("io.open")
#        _ = mocker.patch(
#            "toml.decoder.loads",
#            return_value=toml.dumps(openapi_config.model_dump()),
#        )
#
#        application_errorhandler_mock = MagicMock()
#
#        def app_init_hook(app: AppInjector[FlaskApp]):
#            _ = bind_errorhandler(app.app, code_or_exception_type)(
#                application_errorhandler_mock
#            )
#            # _ = app.app.route("/")(failure_lambda)
#
#        flask_client = openapi_client_configurable(openapi_config, app_init_hook)
#        response = flask_client.client.get("/")
#        #########################################
#
#        assert response.headers[CORRELATION_ID_HEADER]
#        _ = uuid.UUID(response.headers[CORRELATION_ID_HEADER])
#
#
#
#
#
#
#
# FIXME regarding json_logging - check line 53 of
# json_logging.framework.connexion/__init__.py
# looks like `.path` is no longer set on _current_request,
# but json_logging is expecting it.
# openapi_config.logging.format = "plaintext"
class TestOpenAPIMiddleware(CreateApp):
    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___register_api_response_handlers__sets_correlation_id_response_header_when_set_in_request_header(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        openapi_mock_controller.begin()
        flask_client = openapi_client_configurable(openapi_config)
        correlation_id = str(uuid.uuid4())
        response = flask_client.client.get(
            "/", headers={CORRELATION_ID_HEADER: correlation_id}
        )

        assert response.headers[CORRELATION_ID_HEADER] == correlation_id

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__validates_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_request_configurable: RequestConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        correlation_id = "abc123"
        openapi_mock_controller.begin()
        with openapi_request_configurable(
            openapi_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
        ):
            with pytest.raises(
                ValueError, match="^badly formed hexadecimal UUID string$"
            ):
                _ = _get_correlation_id(MagicMock())

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__uses_existing_correlation_id_when_set_in_request_headers(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_request_configurable: RequestConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        openapi_config.logging.format = format
        correlation_id = str(uuid.uuid4())
        openapi_mock_controller.begin()
        with openapi_request_configurable(
            openapi_config, {"headers": {CORRELATION_ID_HEADER: correlation_id}}
        ):
            correlation_id = _get_correlation_id(MagicMock())
            assert correlation_id == correlation_id

    @pytest.mark.parametrize("format", ["plaintext", "JSON"])
    def test___get_correlation_id__sets_correlation_id(
        self,
        format: Literal["plaintext", "JSON"],
        openapi_request_configurable: RequestConfigurable,
        openapi_config: Config,
        openapi_mock_controller: OpenAPIMockController,
    ):
        # app = FlaskApp("foo")
        openapi_config.logging.format = format

        openapi_mock_controller.begin()
        with openapi_request_configurable(openapi_config):
            correlation_id = _get_correlation_id(MagicMock())

            assert correlation_id
            _ = uuid.UUID(correlation_id)

    def test__bind_requesthandler__returns_decorated_flask_request_hook(self):
        app = FlaskApp("foo")

        flask_request_hook_mock = MagicMock()

        wrapped_decorator = bind_requesthandler(app.app, flask_request_hook_mock)
        _ = wrapped_decorator(lambda: None)

        assert flask_request_hook_mock.called

    def test__bind_requesthandler__calls_decorated_function_when_app_is_run(
        self,
        openapi_mock_controller: OpenAPIMockController,
    ):
        app = FlaskApp("foo")

        openapi_mock_controller.begin()

        flask_client = app.test_client()

        wrapped_handler_decorator = bind_requesthandler(app.app, Flask.before_request)
        request_handler_mock = MagicMock()
        _ = wrapped_handler_decorator(request_handler_mock)

        _ = flask_client.get("/")

        assert request_handler_mock.called

    @pytest.mark.parametrize(
        "code_or_exception,openapi_mock_controller",
        [(Exception, lambda: 1), (HTTPException, lambda: 1), (401, lambda: 1)],
        indirect=["openapi_mock_controller"],
    )
    def test__bind_errorhandler__binds_flask_errorhandler(
        self,
        code_or_exception: type[Exception] | int,
        # openapi_client: OpenAPIClientInjector,
        openapi_config: Config,
        openapi_client_configurable: OpenAPIClientInjectorConfigurable,
        openapi_mock_controller: OpenAPIMockController,
        mocker: MockerFixture,
    ):
        flask_errorhandler_mock = mocker.patch("flask.Flask.errorhandler")

        def app_init_hook(app: OpenAPIAppInjector):
            _ = bind_errorhandler(app.app, code_or_exception)

        openapi_mock_controller.begin()
        _ = openapi_client_configurable(openapi_config, app_init_hook)

        flask_errorhandler_mock.assert_called_with(code_or_exception)

    @pytest.mark.parametrize(
        "code_or_exception_type,expected_exception_type,openapi_mock_controller",
        [
            (
                Exception,
                ZeroDivisionError,
                lambda: 1 / 0,  # 1/0 to raise an exception (any exception)
            ),
            (HTTPException, BadRequest, lambda: abort(400)),
            (401, Unauthorized, lambda: abort(401)),
        ],
        indirect=["openapi_mock_controller"],
    )
    def test__bind_errorhandler__calls_decorated_function_with_correct_error_when_error_occurs_during_request(
        self,
        code_or_exception_type: type[Exception] | int,
        expected_exception_type: type[Exception],
        openapi_mock_controller: OpenAPIMockController,
    ):
        app = FlaskApp("foo")
        application_errorhandler_mock = MagicMock()
        _ = bind_errorhandler(app, code_or_exception_type)(
            application_errorhandler_mock
        )

        openapi_mock_controller.begin()
        app.add_api("foo.yaml")

        flask_client = app.test_client()

        _ = flask_client.get("/", headers={"Host": "localhost:5000"})

        assert application_errorhandler_mock.called
        assert isinstance(
            application_errorhandler_mock.call_args[0][0], expected_exception_type
        )
