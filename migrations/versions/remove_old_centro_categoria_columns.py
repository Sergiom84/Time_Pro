"""Remove old centro and categoria columns from user table

Revision ID: remove_old_columns_001
Revises: change_centro_to_fk_001
Create Date: 2025-11-28 00:00:00.000000

Removes the deprecated centro and categoria ENUM columns from the user table.
These have been replaced by center_id and category_id foreign keys.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_old_columns_001'
down_revision = 'change_centro_to_fk_001'
branch_labels = None
depends_on = None


def upgrade():
    # This migration safely removes the old centro and categoria columns
    # if they exist. It's safe to run multiple times.

    conn = op.get_bind()

    # For PostgreSQL, we can use information_schema
    # For SQLite, we use PRAGMA table_info
    if conn.dialect.name == 'postgresql':
        # Check if columns exist in PostgreSQL
        result = conn.execute(sa.text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='user' AND column_name IN ('centro', 'categoria')
        """))
        existing_cols = [row[0] for row in result]

        if 'centro' in existing_cols:
            op.execute('ALTER TABLE "user" DROP COLUMN "centro"')
        if 'categoria' in existing_cols:
            op.execute('ALTER TABLE "user" DROP COLUMN "categoria"')

    elif conn.dialect.name == 'sqlite':
        # SQLite doesn't support DROP COLUMN directly in older versions
        # but we can use batch_alter_table which handles it
        from sqlalchemy import inspect
        inspector = inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('user')]

        if 'centro' in columns or 'categoria' in columns:
            with op.batch_alter_table('user', schema=None) as batch_op:
                if 'centro' in columns:
                    batch_op.drop_column('centro')
                if 'categoria' in columns:
                    batch_op.drop_column('categoria')


def downgrade():
    # Note: This downgrade is intentionally incomplete as we're removing deprecated columns
    # If you need to downgrade, manually add the columns back and populate from FK relationships
    pass
