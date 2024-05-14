from typing import Sequence

from BL_Python.platform.dependency_injection import UserLoaderModule
from BL_Python.platform.identity import Role as DbRole
from BL_Python.platform.identity import User as DbUser
from BL_Python.platform.identity.user_loader import (
    Role,
    TRole,
    UserId,
    UserLoader,
    UserMixin,
)
from injector import Injector
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

    class UserTable(DbUser):
        pass

    class RoleTable(DbRole):
        pass

    user_loader_module = UserLoaderModule(
        loader=UM, roles=Role, user_table=UserTable, role_table=RoleTable
    )

    injector = Injector([user_loader_module])

    user_loader = injector.get(UserLoader[UserMixin[Role]])

    assert user_loader._loader is UM  # pyright: ignore[reportPrivateUsage]
