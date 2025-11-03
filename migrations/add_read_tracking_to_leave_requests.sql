-- Migración para añadir campos de seguimiento de lectura a leave_request
-- y actualizar el enum de estados

-- Primero, alteramos el enum existente para añadir los nuevos estados
ALTER TYPE request_status_enum RENAME TO request_status_enum_old;

CREATE TYPE request_status_enum AS ENUM (
    'Pendiente', 'Aprobado', 'Rechazado', 'Cancelado', 'Enviado', 'Recibido'
);

-- Actualizar la columna para usar el nuevo enum
ALTER TABLE leave_request
    ALTER COLUMN status DROP DEFAULT,
    ALTER COLUMN status TYPE request_status_enum
        USING status::text::request_status_enum,
    ALTER COLUMN status SET DEFAULT 'Pendiente';

-- Eliminar el enum antiguo
DROP TYPE request_status_enum_old;

-- Añadir nuevos campos para seguimiento de lectura
ALTER TABLE leave_request
    ADD COLUMN read_by_admin BOOLEAN DEFAULT FALSE NOT NULL,
    ADD COLUMN read_date TIMESTAMP;

-- Actualizar las solicitudes existentes según su tipo
UPDATE leave_request
SET status = 'Enviado'
WHERE request_type IN ('Baja médica', 'Ausencia justificada', 'Ausencia injustificada')
  AND status = 'Pendiente';

-- Marcar como leídas las solicitudes ya procesadas
UPDATE leave_request
SET read_by_admin = TRUE,
    read_date = approval_date
WHERE status IN ('Aprobado', 'Rechazado');