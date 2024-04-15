from abc import ABC
from typing import Protocol, TypedDict, TypeVar

from sqlalchemy import Constraint, MetaData
from sqlalchemy.engine import Dialect
from sqlalchemy.ext.declarative import DeclarativeMeta

TBase = TypeVar("TBase")


TableArgsDict = TypedDict("TableArgsDict", {"schema": str | None})


class MetaBase(DeclarativeMeta, ABC):
    metadata: MetaData
    __tablename__: str
    __table_args__: tuple[Constraint | TableArgsDict, ...] | TableArgsDict


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


class Op(Protocol):  # pragma: nocover
    @staticmethod
    def get_bind() -> Connection: ...
