"""
Libraries for working with dictionaries.
"""

from __future__ import annotations

from typing import Any, TypeVar, Union

AnyDict = dict[Any, Union[Any, "AnyDict"]]
TKey = TypeVar("TKey")
TValue = TypeVar("TValue")
NestedDict = dict[TKey, Union[TValue, "NestedDict"]]


def merge(a: AnyDict, b: AnyDict, skip_existing: bool = False):
    """
    Recursively merge values from `b` into `a`

    skip_existing: If true, any keys in `b` that already exist in `a` will not be merged.
        This applies recursively. Keys in nested dictionaries will be merged, but any existing keys will not be overwritten.
    """
    for key in b:
        a_val = a.get(key)
        b_val = b.get(key)
        if isinstance(a_val, dict) and isinstance(b_val, dict):
            result = merge(a_val, b_val, skip_existing)  # pyright: ignore[reportUnknownArgumentType]
            if skip_existing and a_val:
                continue
            a[key] = {**a_val, **result}
        else:
            if skip_existing and a_val:
                continue
            a[key] = b_val
    return a
