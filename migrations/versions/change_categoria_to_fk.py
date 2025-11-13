"""Change User.categoria from ENUM to FK to Category table

Revision ID: change_categoria_to_fk_001
Revises: add_role_001
Create Date: 2025-11-13 00:00:00.000000

Migration to support per-client dynamic categories.
Changes from hardcoded ENUM to Foreign Key relationship with Category table.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'change_categoria_to_fk_001'
down_revision = 'add_role_001'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add category_id column (FK to category table) - nullable for migration
    op.add_column(
        'user',
        sa.Column('category_id', sa.Integer, nullable=True)
    )

    # Step 2: Add FK constraint
    op.create_foreign_key(
        'fk_user_category_id',
        'user', 'category',
        ['category_id'], ['id'],
        ondelete='SET NULL'
    )

    # Note: The categoria ENUM column is kept for backward compatibility
    # It will be migrated to category_id via application code (setup_categories.py)


def downgrade():
    # Step 1: Drop FK constraint
    op.drop_constraint('fk_user_category_id', 'user')

    # Step 2: Drop category_id column
    op.drop_column('user', 'category_id')
