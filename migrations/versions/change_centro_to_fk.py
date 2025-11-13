"""Change User.centro from ENUM to FK to Center table

Revision ID: change_centro_to_fk_001
Revises: change_categoria_to_fk_001
Create Date: 2025-11-13 00:00:00.000000

Migration to support per-client dynamic centers.
Changes from hardcoded ENUM to Foreign Key relationship with Center table.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'change_centro_to_fk_001'
down_revision = 'change_categoria_to_fk_001'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add center_id column (FK to center table) - nullable for migration
    op.add_column(
        'user',
        sa.Column('center_id', sa.Integer, nullable=True)
    )

    # Step 2: Add FK constraint
    op.create_foreign_key(
        'fk_user_center_id',
        'user', 'center',
        ['center_id'], ['id'],
        ondelete='SET NULL'
    )

    # Note: The centro ENUM column is kept for backward compatibility
    # It will be migrated to center_id via application code (direct_setup_centers.py)


def downgrade():
    # Step 1: Drop FK constraint
    op.drop_constraint('fk_user_center_id', 'user')

    # Step 2: Drop center_id column
    op.drop_column('user', 'center_id')
