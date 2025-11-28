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
    # Drop old centro column if it exists
    with op.batch_alter_table('user', schema=None) as batch_op:
        try:
            batch_op.drop_column('centro')
        except Exception:
            # Column might not exist in some databases
            pass

    # Drop old categoria column if it exists
    with op.batch_alter_table('user', schema=None) as batch_op:
        try:
            batch_op.drop_column('categoria')
        except Exception:
            # Column might not exist in some databases
            pass


def downgrade():
    # Note: This downgrade is intentionally incomplete as we're removing deprecated columns
    # If you need to downgrade, manually add the columns back and populate from FK relationships
    pass
