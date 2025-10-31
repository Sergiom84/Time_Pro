"""Add theme_preference to User model

Revision ID: add_theme_preference
Revises: 266bd1a2e93b
Create Date: 2025-10-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_theme_preference'
down_revision = '266bd1a2e93b'
branch_labels = None
depends_on = None


def upgrade():
    # Add theme_preference column to user table
    op.add_column('user', sa.Column('theme_preference', sa.String(length=50), nullable=False, server_default='dark-turquoise'))


def downgrade():
    # Remove theme_preference column from user table
    op.drop_column('user', 'theme_preference')
