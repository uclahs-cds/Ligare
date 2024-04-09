from typing import Any, Type

from sqlalchemy.ext.declarative import DeclarativeMeta


def get_schema_from_metabase(base: Type[DeclarativeMeta]):
    table_args: dict[str, Any] | None
    schema_str: str | None = None
    if table_args := getattr(base, "__table_args__", None):
        if schema := table_args.get("schema"):
            schema_str = f"{schema}"

    return schema_str
