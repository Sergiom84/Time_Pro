-- Agregar campo additional_notification_email a la tabla users
-- Fecha: 2025-01-03

ALTER TABLE users ADD COLUMN IF NOT EXISTS additional_notification_email VARCHAR(120);
