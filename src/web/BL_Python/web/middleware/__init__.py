import json
from logging import Logger
from typing import Any, Dict, Union

from flask import Flask, Response
from flask_injector import FlaskInjector
from werkzeug.exceptions import HTTPException, Unauthorized

from .dependency_injection import AppModule

CORRELATION_ID_HEADER = "X-Correlation-ID"
HEADER_COOKIE = "Cookie"


# def _get_correlation_id():
#    try:
#        session[CORRELATION_ID_HEADER] = str(json_logging.get_correlation_id(request))
#        return session[CORRELATION_ID_HEADER]
#    except Exception as e:
#        correlation_id = session.get(CORRELATION_ID_HEADER)
#        if not correlation_id:
#            correlation_id = str(uuid4())
#            session[CORRELATION_ID_HEADER] = correlation_id
#            logging.warning(
#                f'`json_logging` not configured. Generated new UUID "{correlation_id}" for request correlation ID. Error: "{e}"'
#            )
#        return correlation_id
#
#
# def register_api_request_handlers(app: Flask):
#    @app.before_request  # pyright: ignore[reportGeneralTypeIssues]
#    @inject
#    def log_all_api_requests(request: Request, log: Logger):
#        correlation_id = _get_correlation_id()
#
#        request_headers_safe: Dict[str, str] = dict(request.headers)
#
#        if request_headers_safe.get(HEADER_COOKIE):
#            request_headers_safe[HEADER_COOKIE] = re.sub(
#                rf"({app.session_cookie_name or 'session'}=)[^;]+(;|$)",
#                r"\1<redacted>\2",
#                request_headers_safe[HEADER_COOKIE],
#            )
#
#        log.info(
#            f"Incoming request:\n\
#    {request.method} {request.url}\n\
#    Host: {request.host}\n\
#    Remote address: {request.remote_addr}\n\
#    Remote user: {request.remote_user}",
#            extra={
#                "props": {
#                    "correlation_id": correlation_id,
#                    "headers": request_headers_safe,
#                }
#            },
#        )
#
#
# def register_api_response_handlers(app: Flask):
#    # TODO consider moving request/response logging to the WSGI app
#    # apparently Flask may not call this if unhandled exceptions occur
#    @app.after_request  # pyright: ignore[reportGeneralTypeIssues]
#    @inject
#    def ordered_api_response_handers(response: Response, log: Logger):
#        wrap_all_api_responses(response, log)
#        log_all_api_responses(response, log)
#        return response
#
#    def wrap_all_api_responses(response: Response, log: Logger):
#        correlation_id = _get_correlation_id()
#
#        if not response.headers.get("Access-Control-Allow-Origin"):
#            cors_domain = request.headers.get("Origin")
#            if not cors_domain:
#                cors_domain = request.headers.get("Host")
#
#            if cors_domain:
#                response.headers["Access-Control-Allow-Origin"] = cors_domain
#
#        response.headers["Access-Control-Allow-Credentials"] = "true"
#        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
#
#        response.headers[CORRELATION_ID_HEADER] = correlation_id
#
#        response.headers["Content-Security-Policy"] = "default-src 'self'"
#        # Use a permissive CSP for the Swagger UI
#        # https://github.com/swagger-api/swagger-ui/issues/7540
#        if request.path.startswith("/ui/") or (
#            request.url_rule and request.url_rule.endpoint == "/v1./v1_swagger_ui_index"
#        ):
#            response.headers[
#                "Content-Security-Policy"
#            ] = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; script-src 'self' 'unsafe-inline'"
#
#        return response
#
#    def log_all_api_responses(response: Response, log: Logger):
#        correlation_id = _get_correlation_id()
#
#        response_headers_safe: Dict[str, str] = dict(response.headers)
#
#        if response_headers_safe.get(HEADER_COOKIE):
#            response_headers_safe[HEADER_COOKIE] = re.sub(
#                rf"(Set-Cookie: {app.session_cookie_name or 'session'}=)[^;]+(;|$)",
#                r"\1<redacted>\2",
#                response_headers_safe[HEADER_COOKIE],
#            )
#
#        log.info(
#            f"Outgoing response:\n\
#    Status code: {response.status_code}\n\
#    Status: {response.status}",
#            extra={
#                "props": {
#                    "correlation_id": correlation_id,
#                    "headers": response_headers_safe,
#                }
#            },
#        )
#
#        return response
#
#
# pyright: reportUnusedFunction=false
def register_error_handlers(app: Flask):
    @app.errorhandler(Exception)
    def catch_all_catastrophic(error: Exception, log: Logger):
        log.exception(error)

        response = {"status_code": 500, "error_msg": "Unknown error."}
        return response, 500

    @app.errorhandler(HTTPException)
    def catch_all(error: HTTPException, log: Logger):
        log.exception(error)

        response = {
            "status_code": error.code,
            "error_msg": error.description,
            "status": error.name,
        }
        return response, error.code

    @app.errorhandler(401)
    def unauthorized(
        error: Unauthorized, log: Logger
    ) -> Union[Dict[str, int], Response]:
        log.info(error)

        if error.response is None:
            response = {
                "status_code": error.code,
                "error_msg": error.description,
                "status": error.name,
            }
            return response, error.code  # pyright: ignore[reportGeneralTypeIssues]

        response = error.response
        data = {
            "status_code": response.status_code,
            "error_msg": response.data.decode(),
            "status": response.status,
        }
        response.data = json.dumps(data)
        return response  # pyright: ignore[reportGeneralTypeIssues]


# def register_app_teardown_handlers(app: Flask):
#    @app.teardown_request  # pyright: ignore[reportGeneralTypeIssues]
#    @inject
#    def remove_database_sessions(
#        exception: Any, scoped_session: ScopedSession, session: Session, log: Logger
#    ):
#        try:
#            session.rollback()
#        except:
#            log.error(
#                f"Error when rolling back SQLAlchemy Session with id {id(session)} during teardown_request.",
#                exc_info=1,  # pyright: ignore[reportGeneralTypeIssues]
#            )
#
#        try:
#            scoped_session.remove()
#        except:
#            log.error(
#                f"Error when removing Session with id {id(session)} from ScopedSession with id {id(scoped_session)} during teardown_request.",
#                exc_info=1,  # pyright: ignore[reportGeneralTypeIssues]
#            )
#


def configure_dependencies(app: Flask, *args: Any):
    """
    Configures dependency injection and registers all Flask
    application dependencies. The FlaskInjector instance
    can be used to bootstrap and start the Flask application.
    """
    # bootstrap the flask application and its dependencies
    flask_injector = FlaskInjector(
        app,
        [
            AppModule(app, *args),
            # AppSamlModule(
            #    metadata=app.config["SAML2_METADATA"]
            #    or app.config["SAML2_METADATA_URL"],
            #    settings=vars(app.config["SAML2_LOGGING"]),
            # ),
        ],
    )

    return flask_injector
