"""Crear tabla email_notification_log

Revision ID: create_email_log_table
Revises: b6ca4ef471ba
Create Date: 2025-11-06 14:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_email_log_table'
down_revision = 'b6ca4ef471ba'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla email_notification_log
    op.create_table('email_notification_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=20), nullable=False),
        sa.Column('email_to', sa.String(length=120), nullable=False),
        sa.Column('additional_email_to', sa.String(length=120), nullable=True),
        sa.Column('scheduled_time', sa.Time(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Crear índices para mejorar el rendimiento de consultas
    op.create_index('idx_email_log_user_id', 'email_notification_log', ['user_id'])
    op.create_index('idx_email_log_sent_at', 'email_notification_log', ['sent_at'])
    op.create_index('idx_email_log_type_date', 'email_notification_log', ['notification_type', 'sent_at'])


def downgrade():
    # Eliminar índices
    op.drop_index('idx_email_log_type_date', table_name='email_notification_log')
    op.drop_index('idx_email_log_sent_at', table_name='email_notification_log')
    op.drop_index('idx_email_log_user_id', table_name='email_notification_log')

    # Eliminar tabla
    op.drop_table('email_notification_log')
