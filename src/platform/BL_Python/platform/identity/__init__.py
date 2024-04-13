from typing import List, Protocol, Type

from BL_Python.database.schema.metabase import get_schema_from_metabase
from sqlalchemy import Column, ForeignKey, Integer, Unicode
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import RelationshipProperty, relationship
from typing_extensions import override


class Role(Protocol):
    __tablename__: str
    role_id: int
    role_name: str
    users: "list[User]"


class User(Protocol):
    __tablename__: str
    user_id: int
    username: str
    roles: "list[Role]"


class UserRole(Protocol):
    user_id: int
    role_id: int


def get_table_str(tablename: str, base: Type[DeclarativeMeta]):
    schema = get_schema_from_metabase(base)
    schema_str = f"{schema}." if schema else ""
    return f"{schema_str}{tablename}"


class RoleTable:
    def __new__(cls, base: Type[DeclarativeMeta]):
        class Role(base):
            """
            Roles that may be used for access validation.
            """

            __tablename__ = "role"

            role_id = Column("role_id", Integer, primary_key=True)
            role_name = Column("role_name", Unicode, nullable=False, unique=True)

            users: "RelationshipProperty[DeclarativeMeta]" = relationship(
                "User",
                secondary=get_table_str("user_role", base),
                back_populates="roles",
            )

            @override
            def __repr__(self) -> str:
                return "<Role (role_id=%d, role_name=%s)>" % (
                    self.role_id,
                    self.role_name,
                )

        return Role


class UserTable:
    def __new__(cls, base: Type[DeclarativeMeta]):
        class User(base):
            __tablename__ = "user"

            user_id = Column("user_id", Integer, primary_key=True)
            username = Column("username", Unicode, nullable=False, unique=True)

            roles: "List[Role] | RelationshipProperty[List[Role]]" = relationship(
                "Role",
                secondary=get_table_str("user_role", base),
                back_populates="users",
            )

            @override
            def __repr__(self) -> str:
                return "<Role (user_id=%d, username=%s)>" % (
                    self.user_id,
                    self.username,
                )

        return User


class UserRoleTable:
    def __new__(cls, base: Type[DeclarativeMeta]):
        class UserRole(base):
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
                ForeignKey(get_table_str("user.role_id", base)),
                primary_key=True,
            )

            @override
            def __repr__(self) -> str:
                return "<UserRole (user_id=%d, role_id=%d)>" % (
                    self.user_id,
                    self.role_id,
                )

        return UserRole
