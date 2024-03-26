"""
This type stub file was generated by pyright.
"""

from typing import Optional, TYPE_CHECKING, TypeVar, Union
from sqlalchemy import Index, Table, __version__, sql, types as sqltypes
from sqlalchemy.sql.elements import BindParameter, ColumnElement, TextClause
from typing_extensions import TypeGuard
from sqlalchemy.sql.base import _NoneName
from sqlalchemy.util import symbol as _NoneName

if TYPE_CHECKING:
    ...
_CE = TypeVar("_CE", bound=Union["ColumnElement[Any]", "SchemaItem"])
_vers = ...
sqla_13 = ...
sqla_14 = ...
sqla_14_18 = ...
sqla_14_26 = ...
sqla_2 = ...
sqlalchemy_version = __version__
class _Unsupported:
    "Placeholder for unsupported SQLAlchemy classes"
    ...


if sqla_2:
    ...
else:
    ...
_ConstraintName = Union[None, str, _NoneName]
_ConstraintNameDefined = Union[str, _NoneName]
def constraint_name_defined(name: _ConstraintName) -> TypeGuard[_ConstraintNameDefined]:
    ...

def constraint_name_string(name: _ConstraintName) -> TypeGuard[str]:
    ...

def constraint_name_or_none(name: _ConstraintName) -> Optional[str]:
    ...

AUTOINCREMENT_DEFAULT = ...
def url_render_as_string(url, hide_password=...):
    ...

if hasattr(sqltypes.TypeEngine, "_variant_mapping"):
    ...
else:
    ...
class _textual_index_element(sql.ColumnElement):
    """Wrap around a sqlalchemy text() construct in such a way that
    we appear like a column-oriented SQL expression to an Index
    construct.

    The issue here is that currently the Postgresql dialect, the biggest
    recipient of functional indexes, keys all the index expressions to
    the corresponding column expressions when rendering CREATE INDEX,
    so the Index we create here needs to have a .columns collection that
    is the same length as the .expressions collection.  Ultimately
    SQLAlchemy should support text() expressions in indexes.

    See SQLAlchemy issue 3174.

    """
    __visit_name__ = ...
    def __init__(self, table: Table, text: TextClause) -> None:
        ...
    
    def get_children(self): # -> list[Unknown]:
        ...
    


class _literal_bindparam(BindParameter):
    ...


if sqla_14:
    ...
else:
    def create_mock_engine(url, executor, **kw): # -> Engine:
        ...
    
def is_expression_index(index: Index) -> bool:
    ...
