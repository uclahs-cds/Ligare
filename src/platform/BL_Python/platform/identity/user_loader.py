from dataclasses import dataclass
from logging import Logger
from typing import Callable, Type

from injector import inject
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.scoping import ScopedSession

from . import Role, User


@dataclass
class UserId:
    user_id: int
    username: str


from enum import Enum


class UserLoader:
    """
    Class intended for user with FlaskLogin. FlaskLogin is not required.
    """

    @inject
    def __init__(
        self,
        loader: Callable[[UserId, list[Enum]], None],
        roles: Type[Enum],
        user_table: Type[User],
        role_table: Type[Role],
        scoped_session: ScopedSession,
        log: Logger,
    ) -> None:
        """
        Load and optionally create a user.

        :param Callable[[UserId, list[Enum]], None] loader: A callback that receives the create user information including its roles.
        :param Type[Enum] roles: An enum representing possible roles for a user.
        :param Type[User] user_table: The SQLAlchemy table type for a user.
        :param Type[Role] role_table: The SQLAlchemy table type for a role.
        :param ScopedSession scoped_session: The SQLAlchemy connection scope.
        :param Logger log: A Logger instance.
        """
        self._loader = loader
        self._roles = roles
        self._user_table = user_table
        self._role_table = role_table
        self._scoped_session = scoped_session
        self._log = log
        super().__init__()

    def user_loader(
        self, username: str, default_role: Enum, create_if_new_user: bool = False
    ):
        """
        Load a user and its roles from the database.

        :param str username: The users username.
        :param Enum default_role: The default role assigned to the user when `create_if_new_user` is true and the user does not already exist.
        :param bool create_if_new_user: Create the user in the database if it does not already exist, defaults to False.

        :raises AssertionError: If a user is loaded from the database, but it is not of the type specified by user_table.
        """
        session = self._scoped_session()

        self._log.debug(f'Loading user "{username}"')

        if not username:
            self._log.warn("`username` is empty. Skipping load.")
            return

        try:
            user = (
                session.query(self._user_table)
                .join(self._user_table.roles)
                .filter(self._user_table.username == username)
                .options(contains_eager(self._user_table.roles))
                .one_or_none()
            )

            self._log.debug(f'Queried for "{username}" in database')

            if create_if_new_user and user is None:
                self._log.info(
                    f'User "{username}" does not already exist in the database'
                )

                role = (
                    session.query(self._role_table)
                    .filter(self._role_table.role_name == default_role.name)
                    .one()
                )

                user = self._user_table(username=username, roles=[role])

                session.add(user)
                session.commit()

                self._log.info(f'User "{username}" added to the database')
            elif user is None:
                self._log.info(
                    "Username does not exist. Refusing to create a new user. This happens when a username (likely from a cookie)\
     cannot be found in the database, and the process should not create a new user."
                )
                return
            else:
                self._log.debug(f'User "{username}" loaded from the database')

            if not isinstance(user, self._user_table):
                raise AssertionError(
                    f"User object queried from database is unexpected type `{type(user)}`. Expected type `{type(self._user_table)}`."
                )

            user_roles = dict(self._roles.__members__.items())
            roles = [user_roles[user_role.role_name] for user_role in user.roles]

            self._loader(
                UserId(
                    user_id=user.user_id,
                    username=user.username,
                ),
                roles,
            )
        except:
            self._log.exception(
                f'Error when loading user "{username}" from the database.'
            )
            raise
