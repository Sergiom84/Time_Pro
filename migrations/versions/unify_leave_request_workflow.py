"""Unify leave request workflow - remove Recibido status

Revision ID: unify_leave_workflow_001
Revises: remove_old_columns_001
Create Date: 2025-11-29 00:00:00.000000

This migration unifies the leave request workflow by:
- Converting "Enviado" requests to "Pendiente" (awaiting approval)
- Converting "Recibido" requests to "Aprobado" (already acknowledged by admin)
- Eliminating the dual-workflow system
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'unify_leave_workflow_001'
down_revision = 'remove_old_columns_001'
branch_labels = None
depends_on = None


def upgrade():
    """Convert all leave requests to unified Pendiente/Aprobado workflow."""
    conn = op.get_bind()

    # Update "Enviado" (sent but not yet reviewed) to "Pendiente" (awaiting approval)
    op.execute("""
        UPDATE leave_request
        SET status = 'Pendiente'
        WHERE status = 'Enviado'
    """)

    # Update "Recibido" (acknowledged by admin) to "Aprobado" (approved)
    op.execute("""
        UPDATE leave_request
        SET status = 'Aprobado'
        WHERE status = 'Recibido'
    """)


def downgrade():
    """
    Downgrade is not recommended for this migration as it involves data transformation.
    To revert, manually restore from database backup.
    """
    pass
