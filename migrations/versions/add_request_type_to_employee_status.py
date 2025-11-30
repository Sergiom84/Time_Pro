"""Add request_type column to EmployeeStatus for tracking leave request types

Revision ID: add_request_type_001
Revises: change_centro_to_fk_001
Create Date: 2025-11-13 00:00:00.000000

This migration adds a request_type column to track the original type of leave request
(Vacaciones, Baja médica, Ausencia justificada, Ausencia injustificada, Permiso especial)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_request_type_001'
down_revision = 'change_centro_to_fk_001'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna request_type a tabla employee_status
    op.add_column('employee_status', sa.Column('request_type', sa.String(length=50), nullable=True))


def downgrade():
    # Eliminar columna request_type
    op.drop_column('employee_status', 'request_type')
