from typing import Any

from sqlalchemy.ext.declarative import DeclarativeMeta
from typing_extensions import overload


@overload
def get_schema_from_metabase(base: DeclarativeMeta) -> str: ...
@overload
def get_schema_from_metabase(base: type[DeclarativeMeta]) -> str: ...
def get_schema_from_metabase(base: DeclarativeMeta | type[DeclarativeMeta]) -> str:
    table_args: dict[str, Any] | None
    schema_str: str = ""
    if table_args := getattr(base, "__table_args__", None):
        if schema := table_args.get("schema"):
            schema_str = f"{schema}"

    return schema_str
