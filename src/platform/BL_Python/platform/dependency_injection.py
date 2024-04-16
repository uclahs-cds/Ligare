from logging import Logger

from BL_Python.database.dependency_injection import ScopedSessionModule
from BL_Python.platform.identity import Role as DbRole
from BL_Python.platform.identity import User as DbUser
from BL_Python.platform.identity.user_loader import Role, UserLoader, UserMixin
from BL_Python.programming.patterns.dependency_injection import LoggerModule
from flask import Config as Config
from injector import Binder, Module, provider
from sqlalchemy.orm.scoping import ScopedSession
from typing_extensions import override


class UserLoaderModule(Module):
    def __init__(
        self,
        loader: type[UserMixin],
        roles: type[Role],
        user_table: type[DbUser],
        role_table: type[DbRole],
    ) -> None:
        self._loader = loader
        self._roles = roles
        self._user_table = user_table
        self._role_table = role_table
        super().__init__()

    @override
    def configure(self, binder: Binder) -> None:
        binder.install(ScopedSessionModule)
        binder.install(LoggerModule)

    @provider
    def provide_loader(
        self, scoped_session: ScopedSession, log: Logger
    ) -> UserLoader[UserMixin]:
        return UserLoader(
            loader=self._loader,
            roles=self._roles,
            user_table=self._user_table,
            role_table=self._role_table,
            scoped_session=scoped_session,
            log=log,
        )
