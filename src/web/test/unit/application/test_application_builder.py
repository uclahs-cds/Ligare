from flask import Flask
from flask.testing import FlaskClient
from Ligare.web.middleware.dependency_injection import configure_dependencies
from Ligare.web.testing.create_app import ClientInjector, CreateFlaskApp


class TestApplicationBuilder(CreateFlaskApp):
    def test__configure_dependencies__registers_correct_Flask_instance_with_AppModule(
        self, flask_client: ClientInjector[FlaskClient]
    ):
        flask_injector = configure_dependencies(flask_client.client.application)

        flask_app = flask_injector.injector.get(Flask)
        assert flask_app == flask_client.client.application
