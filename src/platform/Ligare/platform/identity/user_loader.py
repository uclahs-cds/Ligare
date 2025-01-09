from dataclasses import dataclass
from enum import Enum
from logging import Logger
from typing import Generic, Protocol, Sequence, Type, TypeVar, cast

from injector import inject
from Ligare.platform.identity import TMetaBase
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import class_mapper  # pyright: ignore[reportUnknownVariableType]
from sqlalchemy.orm import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.scoping import ScopedSession
from typing_extensions import override

from . import Role as DbRole
from . import User as DbUser


@dataclass
class UserId:
    user_id: int
    username: str


class Role(Enum):
    @override
    def __str__(self):
        return self.name


TRole = TypeVar("TRole", bound=Role, covariant=True)


class UserMixin(Protocol[TRole]):
    id: UserId

    # property resolves invariance error by telling
    # pyright this is an immutable "field"
    @property
    def roles(self) -> Sequence[TRole]: ...

    def __init__(self, id: UserId, roles: Sequence[TRole] | None = None) -> None:
        super().__init__()


TUserMixin = TypeVar("TUserMixin", bound=UserMixin[Role])


class UserLoader(Generic[TUserMixin]):
    """
    Class intended for user with FlaskLogin. FlaskLogin is not required.
    """

    @inject
    def __init__(
        self,
        loader: type[TUserMixin],
        roles: Type[Enum],
        user_table: Type[DbUser[TMetaBase]],
        role_table: Type[DbRole[TMetaBase]],
        scoped_session: ScopedSession,
        log: Logger,
    ) -> None:
        """
        Load and optionally create a user.

        :param Callable[[UserId, list[Enum]], None] loader: A callback that receives the create user information including its roles.
        :param Type[Enum] roles: An enum representing possible roles for a user.
        :param Type[DbUser] user_table: The SQLAlchemy table type for a user.
        :param Type[DbRole] role_table: The SQLAlchemy table type for a role.
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
        self, username: str, default_role: Enum | None, create_if_new_user: bool = False
    ) -> None | TUserMixin:
        """
        Load a user and its roles from the database.

        :param str username: The users username.
        :param Enum default_role: The default role assigned to the user when `create_if_new_user` is true and the user does not already exist.
        :param bool create_if_new_user: Create the user in the database if it does not already exist, defaults to False.

        :raises AssertionError: If a user is loaded from the database, but it is not of the type specified by user_table.
        """
        self._log.debug(f'Loading user "{username}"')

        if not username:
            self._log.warning("`username` is empty. Skipping load.")
            return

        with self._scoped_session() as session:
            try:
                # SQLAlchemy generates invalid SQL when attempting an implicit
                # LEFT JOIN between user -> user_role and user_role -> role.
                # As such, we handle the join explicitly by extracting the property
                # relationships and referencing the relevant columns.
                user_table_property_mapper = cast(
                    Mapper, class_mapper(self._user_table)
                )
                user_table_properties = cast(
                    "list[RelationshipProperty[DbRole[DeclarativeMeta]] | ColumnProperty]",
                    user_table_property_mapper.iterate_properties,  # pyright: ignore[reportUnknownMemberType]
                )
                # Only extract the secondary join table (user_role).
                # We find this by matching on the `role` table relationship
                # from the `user` table.
                user_role_table = next(
                    relationship.secondary
                    for relationship in user_table_properties
                    if (entity := getattr(relationship, "entity", None))
                    and entity.class_ == self._role_table
                )

                user = (
                    session.query(self._user_table)
                    # These two `outerjoin` calls define the explicit
                    # join conditions between the `user` and `role` tables,
                    # and the secondary join table `user_role`.
                    .outerjoin(
                        user_role_table,
                        user_role_table.c.user_id == self._user_table.user_id,
                    )
                    .outerjoin(
                        self._role_table,
                        user_role_table.c.role_id == self._role_table.role_id,
                    )
                    .filter(self._user_table.username == username)
                    .one_or_none()
                )

                self._log.debug(f'Queried for "{username}" in database')

                if create_if_new_user and user is None:
                    self._log.info(
                        f'User "{username}" does not already exist in the database'
                    )

                    if default_role is None:
                        user = self._user_table(username=username)
                    else:
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
                roles = cast(
                    Sequence[Role],
                    [user_roles[user_role.role_name] for user_role in user.roles],
                )

                return self._loader(
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
