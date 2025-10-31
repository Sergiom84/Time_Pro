-- Migración manual: Añadir campos de notificaciones por correo al modelo User
-- Ejecutar este script en la base de datos de producción

-- Añadir columnas de notificaciones
ALTER TABLE "user"
ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS notification_days VARCHAR(100),
ADD COLUMN IF NOT EXISTS notification_time_entry TIME,
ADD COLUMN IF NOT EXISTS notification_time_exit TIME;

-- Verificar que las columnas se crearon correctamente
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'user'
-- AND column_name IN ('email_notifications', 'notification_days', 'notification_time_entry', 'notification_time_exit');
