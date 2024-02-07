import pytest
from BL_Python.programming.str import get_random_str
from BL_Python.web.encryption import (
    _EMPTY_SECRET_KEY_MESSAGE,  # pyright:ignore[reportPrivateUsage]
)
from BL_Python.web.encryption import decrypt_flask_cookie, encrypt_flask_cookie
from BL_Python.web.middleware.dependency_injection import AppModule
from flask import Flask
from injector import Injector
from mock import MagicMock


def test__encrypt_flask_cookie__raises_exception_with_empty_secret_key():
    with pytest.raises(Exception, match=rf"^{_EMPTY_SECRET_KEY_MESSAGE}$"):
        _ = encrypt_flask_cookie("", {"foo": "bar"})


def test__decrypt_flask_cookie__raises_exception_with_empty_secret_key():
    with pytest.raises(Exception, match=rf"^{_EMPTY_SECRET_KEY_MESSAGE}$"):
        _ = decrypt_flask_cookie("", "")


def test__encrypt_flask_cookie__returns_serialized_dictionary():
    secret_key = get_random_str(k=26)
    cookie_value = get_random_str(k=26)
    encrypted_cookie = encrypt_flask_cookie(
        secret_key,
        {
            test__encrypt_flask_cookie__returns_serialized_dictionary.__name__: cookie_value
        },
    )

    assert encrypted_cookie
    assert isinstance(encrypted_cookie, str)


def test__decrypt_flask_cookie__returns_correct_cookie_value():
    secret_key = get_random_str(k=26)
    cookie_value = get_random_str(k=26)
    encrypted_cookie = encrypt_flask_cookie(
        secret_key,
        {
            test__decrypt_flask_cookie__returns_correct_cookie_value.__name__: cookie_value
        },
    )
    decrypted_cookie = decrypt_flask_cookie(secret_key, encrypted_cookie)

    assert isinstance(decrypted_cookie, dict)
    assert (
        decrypted_cookie[
            test__decrypt_flask_cookie__returns_correct_cookie_value.__name__
        ]
        == cookie_value
    )


def test__AppModule__binds_extra_dependencies():
    flask_mock = MagicMock(spec=Flask)
    flask_mock.name = f"{test__AppModule__binds_extra_dependencies.__name__}-app_name"
    flask_mock.config = {}
    flask_mock.configure_mock()
    extra_dependency_mock = MagicMock()

    class TestDependencyType: ...

    app_module = AppModule(flask_mock, (TestDependencyType, extra_dependency_mock))

    injector = Injector(app_module)
    resolved_type_instance = injector.get(TestDependencyType)

    assert id(resolved_type_instance) == id(extra_dependency_mock)
