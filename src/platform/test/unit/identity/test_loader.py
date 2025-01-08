from typing import Sequence

from injector import Injector
from Ligare.platform.dependency_injection import UserLoaderModule
from Ligare.platform.identity import Role as DbRole
from Ligare.platform.identity import User as DbUser
from Ligare.platform.identity.user_loader import (
    Role,
    TRole,
    UserId,
    UserLoader,
    UserMixin,
)
from sqlalchemy.ext.declarative import DeclarativeMeta
from typing_extensions import override


def test__UserLoaderModule__uses_application_loader_mixin():
    class UM(UserMixin[TRole]):
        @override
        def __init__(
            self, user_id: UserId, roles: Sequence[TRole] | None = None
        ) -> None:
            self._user_id = user_id
            self._roles = roles
            super().__init__(user_id, roles)

    class UserTable(DbUser[DeclarativeMeta]):
        pass

    class RoleTable(DbRole[DeclarativeMeta]):
        pass

    user_loader_module = UserLoaderModule(
        loader=UM, roles=Role, user_table=UserTable, role_table=RoleTable
    )

    injector = Injector([user_loader_module])

    user_loader = injector.get(UserLoader[UserMixin[Role]])

    assert user_loader._loader is UM  # pyright: ignore[reportPrivateUsage]
