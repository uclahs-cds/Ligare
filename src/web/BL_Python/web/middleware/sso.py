import logging as log
from abc import ABC
from functools import wraps
from typing import Any, Callable, Protocol, Sequence, TypeVar, cast

from BL_Python.platform.identity.user_loader import Role, UserId
from flask_login import LoginManager
from flask_login import UserMixin as FlaskLoginUserMixin
from flask_login import current_user
from flask_login import (
    login_required as flask_login_required,  # pyright: ignore[reportUnknownVariableType]
)
from werkzeug.local import LocalProxy

T = TypeVar("T", contravariant=True)


class AuthCheckOverrideCallable(Protocol):
    def __call__(
        self, user: FlaskLoginUserMixin, *args: Any, **kwargs: Any
    ) -> bool: ...


class LoginUserMixin(FlaskLoginUserMixin, ABC):
    id: UserId
    roles: Sequence[Role]


def login_required(
    roles: Sequence[Role] | Callable[..., Any] | None = None,
    auth_check_override: AuthCheckOverrideCallable | None = None,
):
    """
    Require a valid Flask session before calling the decorated function.

    This method uses the list of `roles` to determine whether the current session user
    has any of the roles listed. Alternatively, the use of `auth_check_override` can is used to
    bypass the role check. If the `auth_check_override` method returns True, the user is considered
    to have access to the decorated API endpoint. If the `auth_check_override` method returns False,
    `login_required` falls back to checking `roles`.

    If `roles` is a list, the user must have been assigned one of the roles specified.
    If `roles` is None, or if the decorator is not explicitly called, this will
    only require a valid Flask session regardless of the user's roles.

    If both `auth_check_override` and `roles` are None, this returns `flask_login.login_required`.
    Call this directly, rather than as a decorator.
    See https://flask-login.readthedocs.io/en/latest/#flask_login.login_required for more information.

    If `roles` is a callable and `auth_check_override` is None, this executes `flask_login.login_required` in its usual way.
    This is the same as using `flask_login.login_required` as a decorator.
    See https://flask-login.readthedocs.io/en/latest/#flask_login.login_required for more information.

    If `roles` is a list of User Roles and the current session user's roles intersect with `roles`,
    this returns True. If the current session user's roles do not intersect with `roles`, this returns False.

    If `auth_check_override` is a callable, it will be called with the following parameters:
        * `user` is the current session user
        * `*args` will be any arguments passed without argument keywords. When using `login_required` as a
          decorator, this will be an empty tuple.
        * `**kwargs` will be any parameters specified with keywords. When using `login_required` as a decorator,
          this will be the parameters passed into the decorated method.
          In the case of a Flask API endpoint, for example, this will be all of the endpoint method parameters.
    """

    if auth_check_override is None:
        if roles is None:
            return cast(Callable[[Callable[..., Any]], Any], flask_login_required)

        # In this case, `roles` is actually a function.
        # It is probably a decorated function.
        if callable(roles):
            return cast(Any, flask_login_required(roles))
    else:
        if not callable(auth_check_override):
            raise TypeError("Override must be a callable.")

    if not isinstance(roles, list):
        raise TypeError("Roles must be a list of User Roles.")

    login_manager = LoginManager()

    def wrapper(fn: Callable[..., Any]):
        @wraps(fn)
        def decorated_view(*args: Any, **kwargs: Any):
            unauthorized = True
            try:
                user = cast(
                    LoginUserMixin, LocalProxy._get_current_object(current_user)
                )  # pyright: ignore[reportPrivateUsage,reportCallIssue]
                if not user.is_authenticated:
                    # this should end up raising a 401 exception
                    return login_manager.unauthorized()

                if callable(auth_check_override):
                    if auth_check_override(user, *args, **kwargs):
                        unauthorized = False

                # if authorization was overriden and successful, don't check roles
                if unauthorized:
                    if not isinstance(roles, list):  # pyright: ignore[reportUnnecessaryIsInstance]
                        # this should end up raising a 401 exception
                        return login_manager.unauthorized()

                    # if roles is empty, no roles will intersect.
                    # this means an empty list means "no roles have access"
                    role_intersection = [
                        role for role in user.roles if role in (roles or [])
                    ]
                    if len(role_intersection) == 0:
                        # this should end up raising a 401 exception
                        return login_manager.unauthorized()
            except Exception as e:
                log.exception(e)
                # this should end up raising a 401 exception
                return login_manager.unauthorized()

            return fn(*args, **kwargs)

        return decorated_view

    return wrapper
