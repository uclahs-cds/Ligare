import json
from logging import Logger
from typing import Awaitable, Callable, TypeVar

from BL_Python.web.middleware.flask import (
    register_flask_api_request_handlers,
    register_flask_api_response_handlers,
)
from BL_Python.web.middleware.openapi import (
    register_openapi_api_request_handlers,
    register_openapi_api_response_handlers,
)
from connexion import FlaskApp
from flask import Flask, Response
from flask.typing import (
    AfterRequestCallable,
    BeforeRequestCallable,
    ResponseReturnValue,
)
from werkzeug.exceptions import HTTPException, Unauthorized

# pyright: reportUnusedFunction=false


# Fixes type problems when using @inject with @app.before_request and @app.after_request.
# The main difference with these types as opposed to the Flask-defined types is that
# these types allow the handler to take any arguments, versus no arguments or just Response.
AfterRequestCallable = Callable[..., Response] | Callable[..., Awaitable[Response]]
BeforeRequestCallable = (
    Callable[..., ResponseReturnValue | None]
    | Callable[..., Awaitable[ResponseReturnValue | None]]
)
T_request_callable = TypeVar(
    "T_request_callable", bound=BeforeRequestCallable | AfterRequestCallable | None
)
# Fixes type problems when using Flask-Injector, which automatically sets up any bound
# error handlers. The error handler types in Flask have the same problem as After/BeforeRequestCallable
# in that their parameters are `[Any]` rather than `...`. This relaxes that. The type
# is valid here because Flask-Injector does actually include the provided types as parameters.
ErrorHandlerCallable = (
    Callable[..., ResponseReturnValue] | Callable[..., Awaitable[ResponseReturnValue]]
)
T_error_handler = TypeVar("T_error_handler", bound=ErrorHandlerCallable)

TFlaskApp = Flask | FlaskApp
T_flask_app = TypeVar("T_flask_app", bound=TFlaskApp)


def bind_errorhandler(
    app: TFlaskApp,
    code_or_exception: type[Exception] | int,
) -> Callable[[T_error_handler], T_error_handler | None]:
    if isinstance(app, Flask):
        return app.errorhandler(code_or_exception)
    else:
        return app.app.errorhandler(code_or_exception)


def register_api_request_handlers(app: TFlaskApp):
    if isinstance(app, Flask):
        return register_flask_api_request_handlers(app)
    else:
        return register_openapi_api_request_handlers(app)


def register_api_response_handlers(app: TFlaskApp):
    if isinstance(app, Flask):
        # TODO consider moving request/response logging to the WSGI app
        # apparently Flask may not call this if unhandled exceptions occur
        return register_flask_api_response_handlers(app)
    else:
        return register_openapi_api_response_handlers(app)


def register_error_handlers(app: TFlaskApp):
    @bind_errorhandler(app, Exception)
    # @inject
    def catch_all_catastrophic(error: Exception, log: Logger):
        # error: connexion.lifecycle.ConnexionRequest, log: ZeroDivisionError
        log.exception(error)

        response = {
            "status_code": 500,
            "error_msg": "Unknown error.",
            "status": "Internal Server Error",
        }
        return response, 500

    @bind_errorhandler(app, HTTPException)
    # @inject
    def catch_all(error: HTTPException, log: Logger):
        log.exception(error)

        response = {
            "status_code": error.code,
            "error_msg": error.description,
            "status": error.name,
        }

        return (
            response,
            error.code if error.code is not None else 500,
        )

    @bind_errorhandler(app, 401)
    # @inject
    def unauthorized(error: Unauthorized, log: Logger):
        log.info(error)

        if error.response is None or not isinstance(error.response, Response):
            response = {
                "status_code": 401,
                "error_msg": error.description,
                "status": error.name,
            }
            return response, 401

        response = error.response
        data = {
            "status_code": response.status_code,
            "error_msg": response.data.decode(),
            "status": response.status,
        }
        response.data = json.dumps(data)
        return response
