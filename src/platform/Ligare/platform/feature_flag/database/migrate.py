"""Add feature flags"""

import sqlalchemy as sa
from alembic.operations.base import Operations
from Ligare.database.schema import get_type_from_op
from sqlalchemy import false

from ..db_feature_flag_router import FeatureFlagTable


# fmt: off
def upgrade(op: Operations):
    dialect = get_type_from_op(op)
    dialect_supports_schemas = dialect.supports_schemas
    get_full_table_name = dialect.get_full_table_name
    get_dialect_schema = dialect.get_dialect_schema
    timestamp_sql = dialect.timestamp_sql

    base_schema_name = get_dialect_schema(FeatureFlagTable) # pyright: ignore[reportArgumentType]
    if dialect_supports_schemas:
        if base_schema_name:
            op.execute(f'CREATE SCHEMA IF NOT EXISTS {base_schema_name}')

    full_table_name = get_full_table_name('feature_flag', FeatureFlagTable) # pyright: ignore[reportArgumentType]
    _ = op.create_table(full_table_name,
    sa.Column('ctime', sa.DateTime(), server_default=sa.text(timestamp_sql), nullable=False),
    sa.Column('mtime', sa.DateTime(), server_default=sa.text(timestamp_sql), nullable=False),
    sa.Column('name', sa.Unicode(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=True, server_default=false()),
    sa.Column('description', sa.Unicode(), nullable=False),
    sa.PrimaryKeyConstraint('name'),
    schema=base_schema_name
    )

    if dialect.DIALECT_NAME == 'postgresql':
        op.execute("""
CREATE OR REPLACE FUNCTION func_update_mtime()
RETURNS TRIGGER LANGUAGE 'plpgsql' AS
'
BEGIN
    NEW.mtime = now();
    RETURN NEW;
END;
';""")

        op.execute(f"""
CREATE TRIGGER trigger_update_mtime
BEFORE UPDATE ON {base_schema_name}.{full_table_name}
FOR EACH ROW EXECUTE PROCEDURE func_update_mtime();""")

    else:
        op.execute(f"""
CREATE TRIGGER IF NOT EXISTS '{full_table_name}.trigger_update_mtime'
BEFORE UPDATE
ON '{full_table_name}'
FOR EACH ROW
BEGIN
    UPDATE '{full_table_name}'
    SET mtime=CURRENT_TIMESTAMP
    WHERE name = NEW.name;
END;""")


def downgrade(op: Operations):
    dialect = get_type_from_op(op)
    get_full_table_name = dialect.get_full_table_name
    get_dialect_schema = dialect.get_dialect_schema

    base_schema_name = get_dialect_schema(FeatureFlagTable) # pyright: ignore[reportArgumentType]
    full_table_name = get_full_table_name('feature_flag', FeatureFlagTable) # pyright: ignore[reportArgumentType]

    if dialect.DIALECT_NAME == 'postgresql':
        op.execute(f'DROP SCHEMA {base_schema_name} CASCADE;')
        op.execute("DROP FUNCTION func_update_mtime;")
        op.execute('COMMIT;')

    else:
        op.execute(f"""DROP TRIGGER '{full_table_name}.trigger_update_mtime';""")
        op.drop_table(full_table_name, schema=base_schema_name)
