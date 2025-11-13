"""Add multi-tenant support: Client table and client_id fields

Revision ID: add_multitenant_001
Revises: create_email_log_20251106
Create Date: 2025-11-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_multitenant_001'
down_revision = 'create_email_log_20251106'
branch_labels = None
depends_on = None


def upgrade():
    # Crear enum para planes
    op.execute("CREATE TYPE plan_enum AS ENUM ('lite', 'pro')")

    # Crear tabla client
    op.create_table('client',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('plan', sa.Enum('lite', 'pro', name='plan_enum'), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )

    # Crear cliente por defecto para datos existentes
    op.execute("""
        INSERT INTO client (id, name, slug, plan, is_active, primary_color, secondary_color, created_at)
        VALUES (1, 'Time Pro', 'timepro', 'pro', true, '#0ea5e9', '#06b6d4', NOW())
    """)

    # Agregar columna client_id a user (temporalmente nullable)
    op.add_column('user', sa.Column('client_id', sa.Integer(), nullable=True))

    # Asignar todos los usuarios existentes al cliente por defecto
    op.execute("UPDATE \"user\" SET client_id = 1")

    # Hacer client_id NOT NULL
    op.alter_column('user', 'client_id', nullable=False)

    # Agregar foreign key
    op.create_foreign_key(
        'fk_user_client_id',
        'user', 'client',
        ['client_id'], ['id'],
        ondelete='CASCADE'
    )

    # Agregar client_id a system_config
    op.add_column('system_config', sa.Column('client_id', sa.Integer(), nullable=True))

    # Asignar configuraciones existentes al cliente por defecto
    op.execute("UPDATE system_config SET client_id = 1")

    # Hacer client_id NOT NULL
    op.alter_column('system_config', 'client_id', nullable=False)

    # Agregar foreign key
    op.create_foreign_key(
        'fk_system_config_client_id',
        'system_config', 'client',
        ['client_id'], ['id'],
        ondelete='CASCADE'
    )

    # Eliminar constraint unique de key (ahora será unique por client_id + key)
    op.drop_constraint('system_config_key_key', 'system_config', type_='unique')

    # Agregar constraint unique compuesto
    op.create_unique_constraint('uix_client_key', 'system_config', ['client_id', 'key'])


def downgrade():
    # Eliminar constraint unique compuesto
    op.drop_constraint('uix_client_key', 'system_config', type_='unique')

    # Restaurar constraint unique de key
    op.create_unique_constraint('system_config_key_key', 'system_config', ['key'])

    # Eliminar foreign key de system_config
    op.drop_constraint('fk_system_config_client_id', 'system_config', type_='foreignkey')

    # Eliminar columna client_id de system_config
    op.drop_column('system_config', 'client_id')

    # Eliminar foreign key de user
    op.drop_constraint('fk_user_client_id', 'user', type_='foreignkey')

    # Eliminar columna client_id de user
    op.drop_column('user', 'client_id')

    # Eliminar tabla client
    op.drop_table('client')

    # Eliminar enum
    op.execute("DROP TYPE plan_enum")
