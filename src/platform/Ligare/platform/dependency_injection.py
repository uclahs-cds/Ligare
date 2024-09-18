from logging import Logger

from flask import Config as Config
from injector import Binder, Module, provider
from Ligare.database.dependency_injection import ScopedSessionModule
from Ligare.database.types import MetaBase
from Ligare.platform.identity import Role as DbRole
from Ligare.platform.identity import User as DbUser
from Ligare.platform.identity.user_loader import Role, UserLoader, UserMixin
from Ligare.programming.patterns.dependency_injection import LoggerModule
from sqlalchemy.orm.scoping import ScopedSession
from typing_extensions import override


class UserLoaderModule(Module):
    _bases: list[MetaBase | type[MetaBase]] | None = None

    def __init__(
        self,
        loader: type[UserMixin[Role]],
        roles: type[Role],
        user_table: type[DbUser],
        role_table: type[DbRole],
        bases: list[MetaBase | type[MetaBase]] | None = None,
    ) -> None:
        self._loader = loader
        self._roles = roles
        self._bases = bases
        self._user_table = user_table
        self._role_table = role_table
        super().__init__()

    @override
    def configure(self, binder: Binder) -> None:
        binder.install(ScopedSessionModule(self._bases))
        binder.install(LoggerModule)

    @provider
    def _provide_user_mixin_loader(  # pyright: ignore[reportUnknownParameterType]
        self, user_loader: UserLoader[UserMixin[Role]]
    ) -> UserLoader[UserMixin]:  # pyright: ignore[reportMissingTypeArgument]
        """
        The weirdness with this method's return type supports usage of the `UserLoader`
        class, which uses `TUserMixin`, which is a TypeVar bound to an
        invariant type (`UserMixin[Role]`).
        That, in turn, supports `LoginManager` using `UserLoader[UserMixin]` as a dependency.
        This is all done because we cannot use a TypeVar for a type registered with Injector,
        but we can use concrete types for generics.
        """
        return user_loader

    @provider
    def _provide_user_mixin_role_loader(
        self, scoped_session: ScopedSession, log: Logger
    ) -> UserLoader[UserMixin[Role]]:
        """
        `UserLoader[UserMixin[Role]]` is the concrete type that is returned to
        dependents of `UserLoader[UserMixin]`.
        """
        return UserLoader(
            loader=self._loader,
            roles=self._roles,
            user_table=self._user_table,
            role_table=self._role_table,
            scoped_session=scoped_session,
            log=log,
        )
