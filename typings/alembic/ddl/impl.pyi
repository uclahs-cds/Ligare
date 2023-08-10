"""
This type stub file was generated by pyright.
"""

from typing import Any, Dict, List, Literal, Optional, Sequence, Set, TYPE_CHECKING, TextIO, Tuple, Type, Union
from sqlalchemy.engine import Connection, Dialect
from sqlalchemy.sql.elements import ClauseElement, ColumnElement, quoted_name
from sqlalchemy.sql.schema import Column, Constraint, ForeignKeyConstraint, Index, Table, UniqueConstraint
from sqlalchemy.sql.selectable import TableClause
from sqlalchemy.sql.type_api import TypeEngine
from .base import _ServerDefault
from ..autogenerate.api import AutogenContext
from ..operations.batch import ApplyBatchImpl, BatchOperationsImpl

if TYPE_CHECKING:
    ...
class ImplMeta(type):
    def __init__(cls, classname: str, bases: Tuple[Type[DefaultImpl]], dict_: Dict[str, Any]) -> None:
        ...
    


_impls: Dict[str, Type[DefaultImpl]] = ...
Params = ...
class DefaultImpl(metaclass=ImplMeta):
    """Provide the entrypoint for major migration operations,
    including database-specific behavioral variances.

    While individual SQL/DDL constructs already provide
    for database-specific implementations, variances here
    allow for entirely different sequences of operations
    to take place for a particular migration, such as
    SQL Server's special 'IDENTITY INSERT' step for
    bulk inserts.

    """
    __dialect__ = ...
    transactional_ddl = ...
    command_terminator = ...
    type_synonyms: Tuple[Set[str], ...] = ...
    type_arg_extract: Sequence[str] = ...
    identity_attrs_ignore: Tuple[str, ...] = ...
    def __init__(self, dialect: Dialect, connection: Optional[Connection], as_sql: bool, transactional_ddl: Optional[bool], output_buffer: Optional[TextIO], context_opts: Dict[str, Any]) -> None:
        ...
    
    @classmethod
    def get_by_dialect(cls, dialect: Dialect) -> Type[DefaultImpl]:
        ...
    
    def static_output(self, text: str) -> None:
        ...
    
    def requires_recreate_in_batch(self, batch_op: BatchOperationsImpl) -> bool:
        """Return True if the given :class:`.BatchOperationsImpl`
        would need the table to be recreated and copied in order to
        proceed.

        Normally, only returns True on SQLite when operations other
        than add_column are present.

        """
        ...
    
    def prep_table_for_batch(self, batch_impl: ApplyBatchImpl, table: Table) -> None:
        """perform any operations needed on a table before a new
        one is created to replace it in batch mode.

        the PG dialect uses this to drop constraints on the table
        before the new one uses those same names.

        """
        ...
    
    @property
    def bind(self) -> Optional[Connection]:
        ...
    
    def execute(self, sql: Union[ClauseElement, str], execution_options: Optional[dict[str, Any]] = ...) -> None:
        ...
    
    def alter_column(self, table_name: str, column_name: str, nullable: Optional[bool] = ..., server_default: Union[_ServerDefault, Literal[False]] = ..., name: Optional[str] = ..., type_: Optional[TypeEngine] = ..., schema: Optional[str] = ..., autoincrement: Optional[bool] = ..., comment: Optional[Union[str, Literal[False]]] = ..., existing_comment: Optional[str] = ..., existing_type: Optional[TypeEngine] = ..., existing_server_default: Optional[_ServerDefault] = ..., existing_nullable: Optional[bool] = ..., existing_autoincrement: Optional[bool] = ..., **kw: Any) -> None:
        ...
    
    def add_column(self, table_name: str, column: Column[Any], schema: Optional[Union[str, quoted_name]] = ...) -> None:
        ...
    
    def drop_column(self, table_name: str, column: Column[Any], schema: Optional[str] = ..., **kw) -> None:
        ...
    
    def add_constraint(self, const: Any) -> None:
        ...
    
    def drop_constraint(self, const: Constraint) -> None:
        ...
    
    def rename_table(self, old_table_name: str, new_table_name: Union[str, quoted_name], schema: Optional[Union[str, quoted_name]] = ...) -> None:
        ...
    
    def create_table(self, table: Table) -> None:
        ...
    
    def drop_table(self, table: Table) -> None:
        ...
    
    def create_index(self, index: Index) -> None:
        ...
    
    def create_table_comment(self, table: Table) -> None:
        ...
    
    def drop_table_comment(self, table: Table) -> None:
        ...
    
    def create_column_comment(self, column: ColumnElement[Any]) -> None:
        ...
    
    def drop_index(self, index: Index) -> None:
        ...
    
    def bulk_insert(self, table: Union[TableClause, Table], rows: List[dict], multiinsert: bool = ...) -> None:
        ...
    
    def compare_type(self, inspector_column: Column[Any], metadata_column: Column) -> bool:
        """Returns True if there ARE differences between the types of the two
        columns. Takes impl.type_synonyms into account between retrospected
        and metadata types
        """
        ...
    
    def compare_server_default(self, inspector_column, metadata_column, rendered_metadata_default, rendered_inspector_default):
        ...
    
    def correct_for_autogen_constraints(self, conn_uniques: Set[UniqueConstraint], conn_indexes: Set[Index], metadata_unique_constraints: Set[UniqueConstraint], metadata_indexes: Set[Index]) -> None:
        ...
    
    def cast_for_batch_migrate(self, existing, existing_transfer, new_type): # -> None:
        ...
    
    def render_ddl_sql_expr(self, expr: ClauseElement, is_server_default: bool = ..., **kw: Any) -> str:
        """Render a SQL expression that is typically a server default,
        index expression, etc.

        .. versionadded:: 1.0.11

        """
        ...
    
    def correct_for_autogen_foreignkeys(self, conn_fks: Set[ForeignKeyConstraint], metadata_fks: Set[ForeignKeyConstraint]) -> None:
        ...
    
    def autogen_column_reflect(self, inspector, table, column_info): # -> None:
        """A hook that is attached to the 'column_reflect' event for when
        a Table is reflected from the database during the autogenerate
        process.

        Dialects can elect to modify the information gathered here.

        """
        ...
    
    def start_migrations(self) -> None:
        """A hook called when :meth:`.EnvironmentContext.run_migrations`
        is called.

        Implementations can set up per-migration-run state here.

        """
        ...
    
    def emit_begin(self) -> None:
        """Emit the string ``BEGIN``, or the backend-specific
        equivalent, on the current connection context.

        This is used in offline mode and typically
        via :meth:`.EnvironmentContext.begin_transaction`.

        """
        ...
    
    def emit_commit(self) -> None:
        """Emit the string ``COMMIT``, or the backend-specific
        equivalent, on the current connection context.

        This is used in offline mode and typically
        via :meth:`.EnvironmentContext.begin_transaction`.

        """
        ...
    
    def render_type(self, type_obj: TypeEngine, autogen_context: AutogenContext) -> Union[str, Literal[False]]:
        ...
    
    def create_index_sig(self, index: Index) -> Tuple[Any, ...]:
        ...
    

