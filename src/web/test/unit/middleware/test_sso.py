from typing import Any, Generic, Sequence, cast
from unittest.mock import MagicMock

import pytest
from BL_Python.platform.identity.user_loader import Role, TRole, UserId
from BL_Python.programming.str import get_random_str
from BL_Python.web.encryption import encrypt_flask_cookie
from BL_Python.web.middleware.sso import (
    AuthCheckUser,
    apikey_auth,
    get_username,
    login_required,
)
from BL_Python.web.testing.create_app import CreateOpenAPIApp, OpenAPIClientInjector
from connexion import FlaskApp
from flask import session
from flask_login import UserMixin
from flask_login import login_required as flask_login_required
from pytest_mock import MockerFixture
from typing_extensions import override
from werkzeug.exceptions import Unauthorized


class TestRole(Role):
    Role1 = 1
    Role2 = 2


class TestUser(UserMixin, Generic[TRole]):
    """
    Represents the user object stored in a session.
    """

    id: UserId
    roles: Sequence[TRole]

    @override
    def __init__(self, id: UserId, roles: Sequence[TRole] | None = None):
        super().__init__()
        if roles is None:
            roles = []

        self.id = id
        self.roles = roles


class TestSSO(CreateOpenAPIApp):
    def test__sso__login_required__raises_when_auth_check_override_is_not_callable_and_not_none(
        self,
    ):
        with pytest.raises(TypeError):
            _ = login_required(auth_check_override=True)  # pyright: ignore[reportArgumentType]

    def test__sso__login_required__returns_flask_login_required_when_auth_check_override_is_none_and_roles_is_none(
        self,
    ):
        result = login_required()
        assert result == flask_login_required

    def test__sso__login_required__returns_flask_login_required_decorated_function_when_auth_check_override_is_none_and_roles_is_callable(
        self, mocker: MockerFixture
    ):
        flask_login_required_mock = mocker.patch(
            "BL_Python.web.middleware.sso.flask_login_required"
        )

        def func():
            pass

        _ = login_required(func)
        flask_login_required_mock.assert_any_call(func)

    def test__sso__login_required__throws_when_auth_check_override_is_none_and_roles_is_not_callable_or_not_a_Sequence_or_not_none(
        self, mocker: MockerFixture
    ):
        with pytest.raises(TypeError):
            _ = login_required(auth_check_override=None, roles=True)  # pyright: ignore[reportArgumentType]

    def test__sso__login_required__throws_when_auth_check_override_is_callable_and_roles_is_not_a_Sequence(
        self,
    ):
        with pytest.raises(TypeError):
            _ = login_required(auth_check_override=lambda: None, roles=None)  # pyright: ignore[reportArgumentType]

    def test__sso__login_required__returns_function_decorator(
        self,
    ):
        def auth_check_override(
            user: AuthCheckUser, *args: Any, **kwargs: Any
        ) -> bool: ...

        def func(): ...

        decorator = login_required(
            auth_check_override=auth_check_override,
            roles=[TestRole.Role1, TestRole.Role2],
        )

        decorated_func = decorator(func)
        assert callable(decorated_func)
        assert decorated_func.__wrapped__ == func  # pyright: ignore[reportFunctionMemberAccess]

    def test__sso__login_required__raises_401_when_user_not_authenticated(
        self, openapi_client: OpenAPIClientInjector
    ):
        def auth_check_override(
            user: AuthCheckUser, *args: Any, **kwargs: Any
        ) -> bool: ...

        decorator = login_required(
            auth_check_override=auth_check_override,
            roles=[TestRole.Role1, TestRole.Role2],
        )

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )
        result = openapi_client.client.get("/route")

        assert result.status_code == 401

    def test__sso__login_required__returns_status_200_when_auth_check_override_returns_true(
        self, openapi_client: OpenAPIClientInjector, mocker: MockerFixture
    ):
        def auth_check_override(user: AuthCheckUser, *args: Any, **kwargs: Any) -> bool:
            return True

        decorator = login_required(auth_check_override=auth_check_override, roles=[])

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=None
        ):
            result = openapi_client.client.get("/route")

        assert result.status_code == 200

    def test__sso__login_required__raises_401_when_auth_check_override_returns_false(
        self, openapi_client: OpenAPIClientInjector, mocker: MockerFixture
    ):
        def auth_check_override(user: AuthCheckUser, *args: Any, **kwargs: Any) -> bool:
            return False

        decorator = login_required(auth_check_override=auth_check_override, roles=[])

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=None
        ):
            result = openapi_client.client.get("/route")

        assert result.status_code == 401

    def test__sso__login_required__returns_status_200_when_auth_check_override_returns_false_and_user_has_sufficient_roles(
        self, openapi_client: OpenAPIClientInjector, mocker: MockerFixture
    ):
        def auth_check_override(user: AuthCheckUser, *args: Any, **kwargs: Any) -> bool:
            return False

        decorator = login_required(
            auth_check_override=auth_check_override, roles=[TestRole.Role2]
        )

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=[TestRole.Role2]
        ):
            result = openapi_client.client.get("/route")

        assert result.status_code == 200

    @pytest.mark.parametrize("roles", [None, [], "", 0, 1])
    def test__sso__login_required__raises_401_when_unauthorized_user_has_no_roles(
        self,
        roles: Sequence[Any] | None,
        openapi_client: OpenAPIClientInjector,
        mocker: MockerFixture,
    ):
        def auth_check_override(user: AuthCheckUser, *args: Any, **kwargs: Any) -> bool:
            return False

        decorator = login_required(
            auth_check_override=auth_check_override,
            roles=[TestRole.Role1, TestRole.Role2],
        )

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=roles
        ):
            result = openapi_client.client.get("/route")

        assert result.status_code == 401

    def test__sso__login_required__raises_401_when_unauthorized_user_lacks_sufficient_roles(
        self,
        openapi_client: OpenAPIClientInjector,
        mocker: MockerFixture,
    ):
        def auth_check_override(user: AuthCheckUser, *args: Any, **kwargs: Any) -> bool:
            return False

        decorator = login_required(
            auth_check_override=auth_check_override,
            roles=[TestRole.Role1],
        )

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=[TestRole.Role2]
        ):
            result = openapi_client.client.get("/route")

        assert result.status_code == 401

    @pytest.mark.parametrize("user_roles", [[TestRole.Role2], (TestRole.Role2,)])
    def test__sso__login_required__returns_200_when_unauthorized_user_has_sufficient_roles(
        self,
        user_roles: Sequence[TestRole],
        openapi_client: OpenAPIClientInjector,
        mocker: MockerFixture,
    ):
        def auth_check_override(user: AuthCheckUser, *args: Any, **kwargs: Any) -> bool:
            return False

        decorator = login_required(
            auth_check_override=auth_check_override,
            roles=user_roles,
        )

        def route():
            return [True]

        decorated_func = decorator(route)
        cast(FlaskApp, openapi_client.client.app).add_url_rule(
            "/route", "route", decorated_func
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=[TestRole.Role2]
        ):
            result = openapi_client.client.get("/route")

        assert result.status_code == 200

    def test__sso__get_username__returns_username(
        self,
        openapi_client: OpenAPIClientInjector,
        mocker: MockerFixture,
    ):
        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=None
        ):
            username = get_username(MagicMock())

        assert "username" in username
        assert username["username"] == "test user"

    def test__sso__apikey_auth__returns_username(
        self,
        openapi_client: OpenAPIClientInjector,
        mocker: MockerFixture,
    ):
        token = cast(
            str, cast(FlaskApp, openapi_client.client.app).app.config["SECRET_KEY"]
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=None
        ):
            cookie = encrypt_flask_cookie(
                token, {"_id": session["_id"], "username": "test user"}
            )
            username = apikey_auth(cookie, None)

        assert "username" in username
        assert username["username"] == "test user"

    def test__sso__apikey_auth__raises_401_when_session_is_invalid(
        self,
        openapi_client: OpenAPIClientInjector,
        mocker: MockerFixture,
    ):
        token = cast(
            str, cast(FlaskApp, openapi_client.client.app).app.config["SECRET_KEY"]
        )

        with self.get_authenticated_request_context(
            openapi_client, TestUser, mocker, roles=None
        ):
            cookie = encrypt_flask_cookie(
                token, {"_id": get_random_str(), "username": "test user"}
            )
            with pytest.raises(Unauthorized):
                _ = apikey_auth(cookie, None)
