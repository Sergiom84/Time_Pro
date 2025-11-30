"""Fix audit system: Allow admin to delete/modify records without FK errors

Revision ID: fix_audit_system_001
Revises: unify_leave_workflow_001
Create Date: 2025-11-30 21:00:00.000000

Changes:
1. Drop FK constraint from time_record_audit_log to allow records to be deleted
2. Modify audit_time_record_changes() trigger to skip DELETE operations
   - Still logs INSERT and UPDATE
   - No longer logs DELETE operations

This allows admins to:
- Delete time_records without FK constraint errors
- Modify time_records without errors
- Audit log shows only final state (not intermediate changes)
- Excel export shows only final state without modification indicators
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_audit_system_001'
down_revision = 'unify_leave_workflow_001'
branch_labels = None
depends_on = None


def upgrade():
    # Paso 1: Eliminar FK constraint que impide eliminar registros
    op.execute("""
        ALTER TABLE time_record_audit_log
        DROP CONSTRAINT IF EXISTS time_record_audit_log_time_record_id_fkey;
    """)

    # Paso 2: Modificar función del trigger para ignorar DELETE operations
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_time_record_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                INSERT INTO time_record_audit_log (
                    time_record_id, operation, changed_by_user_id, changed_at, new_values, ip_address
                ) VALUES (
                    NEW.id, 'INSERT', NEW.modified_by, NOW(),
                    jsonb_build_object(
                        'date', NEW.date,
                        'check_in', NEW.check_in,
                        'check_out', NEW.check_out,
                        'notes', NEW.notes,
                        'admin_notes', NEW.admin_notes,
                        'is_active', NEW.is_active,
                        'correction_reason', NEW.correction_reason
                    ),
                    NEW.ip_address
                );
                RETURN NEW;

            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO time_record_audit_log (
                    time_record_id, operation, changed_by_user_id, changed_at,
                    old_values, new_values, change_reason, ip_address
                ) VALUES (
                    NEW.id, 'UPDATE', NEW.modified_by, NOW(),
                    jsonb_build_object(
                        'date', OLD.date,
                        'check_in', OLD.check_in,
                        'check_out', OLD.check_out,
                        'notes', OLD.notes,
                        'admin_notes', OLD.admin_notes,
                        'is_active', OLD.is_active,
                        'correction_reason', OLD.correction_reason
                    ),
                    jsonb_build_object(
                        'date', NEW.date,
                        'check_in', NEW.check_in,
                        'check_out', NEW.check_out,
                        'notes', NEW.notes,
                        'admin_notes', NEW.admin_notes,
                        'is_active', NEW.is_active,
                        'correction_reason', NEW.correction_reason
                    ),
                    NEW.correction_reason,
                    NEW.ip_address
                );
                RETURN NEW;

            ELSIF (TG_OP = 'DELETE') THEN
                -- NO registrar DELETE - el admin puede eliminar registros sin dejar log
                RETURN OLD;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    # Paso 1: Restaurar la función del trigger a su versión original
    # Nota: Esto asume que la función anterior registraba DELETE operations
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_time_record_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                INSERT INTO time_record_audit_log (
                    time_record_id, operation, changed_by_user_id, changed_at, new_values, ip_address
                ) VALUES (
                    NEW.id, 'INSERT', NEW.modified_by, NOW(),
                    jsonb_build_object(
                        'date', NEW.date,
                        'check_in', NEW.check_in,
                        'check_out', NEW.check_out,
                        'notes', NEW.notes,
                        'admin_notes', NEW.admin_notes,
                        'is_active', NEW.is_active,
                        'correction_reason', NEW.correction_reason
                    ),
                    NEW.ip_address
                );
                RETURN NEW;

            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO time_record_audit_log (
                    time_record_id, operation, changed_by_user_id, changed_at,
                    old_values, new_values, change_reason, ip_address
                ) VALUES (
                    NEW.id, 'UPDATE', NEW.modified_by, NOW(),
                    jsonb_build_object(
                        'date', OLD.date,
                        'check_in', OLD.check_in,
                        'check_out', OLD.check_out,
                        'notes', OLD.notes,
                        'admin_notes', OLD.admin_notes,
                        'is_active', OLD.is_active,
                        'correction_reason', OLD.correction_reason
                    ),
                    jsonb_build_object(
                        'date', NEW.date,
                        'check_in', NEW.check_in,
                        'check_out', NEW.check_out,
                        'notes', NEW.notes,
                        'admin_notes', NEW.admin_notes,
                        'is_active', NEW.is_active,
                        'correction_reason', NEW.correction_reason
                    ),
                    NEW.correction_reason,
                    NEW.ip_address
                );
                RETURN NEW;

            ELSIF (TG_OP = 'DELETE') THEN
                INSERT INTO time_record_audit_log (
                    time_record_id, operation, changed_by_user_id, changed_at, old_values
                ) VALUES (
                    OLD.id, 'DELETE', OLD.modified_by, NOW(),
                    jsonb_build_object(
                        'date', OLD.date,
                        'check_in', OLD.check_in,
                        'check_out', OLD.check_out,
                        'notes', OLD.notes,
                        'admin_notes', OLD.admin_notes,
                        'is_active', OLD.is_active,
                        'correction_reason', OLD.correction_reason
                    )
                );
                RETURN OLD;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Paso 2: Restaurar FK constraint
    op.execute("""
        ALTER TABLE time_record_audit_log
        ADD CONSTRAINT time_record_audit_log_time_record_id_fkey
        FOREIGN KEY (time_record_id) REFERENCES time_record(id) ON DELETE CASCADE;
    """)
