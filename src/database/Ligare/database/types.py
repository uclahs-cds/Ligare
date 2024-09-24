from abc import ABC
from typing import Any, Callable, Protocol, TypedDict, TypeVar

from Ligare.database.config import DatabaseConnectArgsConfig
from sqlalchemy import Constraint, MetaData
from sqlalchemy.engine import Dialect
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.scoping import ScopedSession
from sqlalchemy.orm.session import sessionmaker

TBase = TypeVar("TBase")


TableArgsDict = TypedDict("TableArgsDict", {"schema": str | None})


class MetaBase(DeclarativeMeta, ABC):
    metadata: MetaData
    __tablename__: str
    __table_args__: tuple[Constraint | TableArgsDict, ...] | TableArgsDict


T_scoped_session = TypeVar("T_scoped_session", bound=ScopedSession, covariant=True)


class IScopedSessionFactory(Protocol[T_scoped_session]):
    @staticmethod
    def create(
        connection_string: str,
        echo: bool = False,
        execution_options: dict[str, Any] | None = None,
        connect_args: DatabaseConnectArgsConfig | None = None,
        bases: list[MetaBase | type[MetaBase]] | None = None,
    ) -> T_scoped_session: ...

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        session_factory: Callable[..., Any] | "sessionmaker[Any]",
        scopefunc: Any = None,
    ) -> None: ...


class TableNameCallback(Protocol):
    def __call__(  # pragma: nocover
        self,
        dialect_schema: str | None,
        full_table_name: str,
        base_table: str,
        meta_base: MetaBase,
    ) -> None: ...


class Connection(ABC):
    dialect: Dialect
