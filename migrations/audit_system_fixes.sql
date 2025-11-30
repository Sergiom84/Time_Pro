-- Audit System Fixes - Solución para permitir admin eliminar/modificar registros sin errores
-- Fecha: 2025-11-30
-- Descripción: Modificaciones a la auditoría para permitir que admins eliminen y modifiquen
-- registros de time_record sin errores de FK constraint

-- CAMBIO 1: Eliminar FK constraint de time_record_audit_log
-- Esto permite que los registros de auditoría existan sin FK a time_record
ALTER TABLE time_record_audit_log
DROP CONSTRAINT IF EXISTS time_record_audit_log_time_record_id_fkey;

-- CAMBIO 2: Modificar trigger para NO registrar DELETE operations
-- El trigger ahora solo registra INSERT y UPDATE, ignorando DELETE
-- Esto permite que admin elimine registros sin dejar rastro de auditoría

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

-- RESULTADOS ESPERADOS:
-- 1. Admin puede eliminar time_record sin error de FK constraint
-- 2. Admin puede modificar time_record sin error
-- 3. Audit log registra estado FINAL de UPDATEs, no cambios intermedios
-- 4. Audit log NO contiene registros de DELETE
-- 5. Excel export muestra solo estado final sin indicadores de modificación
