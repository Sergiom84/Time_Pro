"""Add role column to User model to distinguish admin types by plan

Revision ID: add_role_001
Revises: add_multitenant_001
Create Date: 2025-11-13 00:00:00.000000

LITE plan: only has 'admin' (single admin per company)
PRO plan: has 'admin' and 'super_admin' (super_admin manages all, admin manages center)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_role_001'
down_revision = 'add_multitenant_001'
branch_labels = None
depends_on = None


def upgrade():
    # Crear enum para roles
    op.execute("CREATE TYPE role_enum AS ENUM ('admin', 'super_admin')")

    # Agregar columna role a la tabla user
    op.add_column('user', sa.Column('role', sa.Enum('admin', 'super_admin', name='role_enum'), nullable=True))

    # Migrar datos: si is_admin=true, asignar role='admin'
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE is_admin = true")

    # Eliminar columna is_admin (ya no la necesitamos)
    op.drop_column('user', 'is_admin')


def downgrade():
    # Restaurar la columna is_admin
    op.add_column('user', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Migrar datos de vuelta: si role='admin', asignar is_admin=true
    op.execute("UPDATE \"user\" SET is_admin = true WHERE role IS NOT NULL")

    # Eliminar columna role
    op.drop_column('user', 'role')

    # Eliminar enum role_enum
    op.execute("DROP TYPE role_enum")
