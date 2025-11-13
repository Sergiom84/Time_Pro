"""Add admin_notes fields to TimeRecord, EmployeeStatus, and LeaveRequest

Revision ID: add_admin_notes_001
Revises: add_request_type_001
Create Date: 2025-11-13 00:00:00.000000

This migration adds admin_notes column to allow administrators to add their own
notes to time records, employee status changes, and leave requests.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_admin_notes_001'
down_revision = 'add_request_type_001'
branch_labels = None
depends_on = None


def upgrade():
    # Add admin_notes to time_record table
    op.add_column('time_record', sa.Column('admin_notes', sa.Text(), nullable=True))

    # Add admin_notes to employee_status table
    op.add_column('employee_status', sa.Column('admin_notes', sa.Text(), nullable=True))

    # Add admin_notes to leave_request table
    op.add_column('leave_request', sa.Column('admin_notes', sa.Text(), nullable=True))


def downgrade():
    # Remove admin_notes from leave_request table
    op.drop_column('leave_request', 'admin_notes')

    # Remove admin_notes from employee_status table
    op.drop_column('employee_status', 'admin_notes')

    # Remove admin_notes from time_record table
    op.drop_column('time_record', 'admin_notes')
