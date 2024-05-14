from abc import ABC
from typing import List, Type, cast

from BL_Python.database.schema.metabase import get_schema_from_metabase
from sqlalchemy import Column, ForeignKey, Integer, Unicode
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty, relationship
from typing_extensions import override


class Role(ABC):
    __tablename__: str

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        /,
        role_id: int = 0,
        role_name: str = "",
        users: "list[User]" = [],  # pyright: ignore[reportCallInDefaultInitializer]
    ) -> None:
        raise NotImplementedError(
            f"`{Role.__class__.__name__}` should only be used for type checking."
        )

    role_id: int
    role_name: str
    users: "list[User]"


class User(ABC):
    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        /,
        user_id: int = 0,
        username: str = "",
        roles: "list[Role]" = [],  # pyright: ignore[reportCallInDefaultInitializer]
    ) -> None:
        raise NotImplementedError(
            f"`{User.__class__.__name__}` should only be used for type checking."
        )

    __tablename__: str
    user_id: int
    username: str
    roles: "list[Role]"


class UserRole(ABC):
    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self, /, user_id: int = 0, role_id: int = 0
    ) -> None:
        raise NotImplementedError(
            f"`{UserRole.__class__.__name__}` should only be used for type checking."
        )

    user_id: int
    role_id: int


def get_table_str(tablename: str, base: Type[DeclarativeMeta]):
    schema = get_schema_from_metabase(base)
    schema_str = f"{schema}." if schema else ""
    return f"{schema_str}{tablename}"


class RoleTable:
    def __new__(cls, base: Type[DeclarativeMeta]) -> type[Role]:
        class _Role(base):
            """
            Roles that may be used for access validation.
            """

            __tablename__ = "role"

            role_id = Column("role_id", Integer, primary_key=True)
            role_name = Column("role_name", Unicode, nullable=False, unique=True)

            users: "RelationshipProperty[DeclarativeMeta]" = relationship(
                "_User",
                secondary=get_table_str("user_role", base),
                back_populates="roles",
            )

            @override
            def __repr__(self) -> str:
                return "<Role (role_id=%d, role_name=%s)>" % (
                    self.role_id,
                    self.role_name,
                )

        return cast(type[Role], _Role)


class UserTable:
    def __new__(cls, base: Type[DeclarativeMeta]) -> type[User]:
        class _User(base):
            __tablename__ = "user"

            user_id = Column("user_id", Integer, primary_key=True)
            username = Column("username", Unicode, nullable=False, unique=True)

            roles: "List[Role] | RelationshipProperty[List[Role]]" = relationship(
                "_Role",
                secondary=get_table_str("user_role", base),
                back_populates="users",
            )

            @override
            def __repr__(self) -> str:
                return "<Role (user_id=%d, username=%s)>" % (
                    self.user_id,
                    self.username,
                )

        return cast(type[User], _User)


class UserRoleTable:
    def __new__(cls, base: Type[DeclarativeMeta]) -> type[UserRole]:
        class _UserRole(base):
            __tablename__ = "user_role"

            user_id = Column(
                "user_id",
                Integer,
                ForeignKey(get_table_str("user.user_id", base)),
                primary_key=True,
            )
            role_id = Column(
                "role_id",
                Integer,
                ForeignKey(get_table_str("role.role_id", base)),
                primary_key=True,
            )

            @override
            def __repr__(self) -> str:
                return "<UserRole (user_id=%d, role_id=%d)>" % (
                    self.user_id,
                    self.role_id,
                )

        return cast(type[UserRole], _UserRole)
