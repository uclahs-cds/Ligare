from typing import Protocol, TypedDict

from sqlalchemy import Constraint, MetaData

TableArgsDict = TypedDict("TableArgsDict", {"schema": str | None})


class MetaBase(Protocol):
    metadata: MetaData
    __tablename__: str
    __table_args__: tuple[Constraint | TableArgsDict, ...] | TableArgsDict
