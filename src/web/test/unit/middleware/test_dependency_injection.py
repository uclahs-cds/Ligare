from flask import Flask
from injector import Injector
from Ligare.web.middleware.dependency_injection import AppModule
from mock import MagicMock


def test__AppModule__binds_extra_dependencies():
    flask_mock = MagicMock(spec=Flask)
    flask_mock.name = f"{test__AppModule__binds_extra_dependencies.__name__}-app_name"
    flask_mock.config = {}
    extra_dependency_mock = MagicMock()

    class TestDependencyType: ...

    app_module = AppModule(flask_mock, (TestDependencyType, extra_dependency_mock))

    injector = Injector(app_module)
    resolved_type_instance = injector.get(TestDependencyType)

    assert id(resolved_type_instance) == id(extra_dependency_mock)
