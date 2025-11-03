-- ============================================================
-- MIGRACIÓN: Añadir campos para adjuntar justificantes
-- Fecha: 2025-11-03
-- Descripción: Permite adjuntar PDFs y fotos a pausas y solicitudes
-- ============================================================

-- 1. Añadir campos a la tabla work_pause
ALTER TABLE work_pause
ADD COLUMN IF NOT EXISTS attachment_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS attachment_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS attachment_size INTEGER;

COMMENT ON COLUMN work_pause.attachment_url IS 'URL del archivo adjunto en Supabase Storage';
COMMENT ON COLUMN work_pause.attachment_filename IS 'Nombre original del archivo';
COMMENT ON COLUMN work_pause.attachment_type IS 'Tipo MIME del archivo (application/pdf, image/jpeg, etc.)';
COMMENT ON COLUMN work_pause.attachment_size IS 'Tamaño del archivo en bytes';

-- 2. Añadir campos a la tabla leave_request
ALTER TABLE leave_request
ADD COLUMN IF NOT EXISTS attachment_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS attachment_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS attachment_size INTEGER;

COMMENT ON COLUMN leave_request.attachment_url IS 'URL del archivo adjunto en Supabase Storage';
COMMENT ON COLUMN leave_request.attachment_filename IS 'Nombre original del archivo';
COMMENT ON COLUMN leave_request.attachment_type IS 'Tipo MIME del archivo (application/pdf, image/jpeg, etc.)';
COMMENT ON COLUMN leave_request.attachment_size IS 'Tamaño del archivo en bytes';

-- 3. Crear índices para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_work_pause_attachment
ON work_pause(attachment_url)
WHERE attachment_url IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_leave_request_attachment
ON leave_request(attachment_url)
WHERE attachment_url IS NOT NULL;

-- 4. Verificar que las columnas se crearon correctamente
SELECT
    'work_pause' as tabla,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'work_pause'
  AND column_name LIKE 'attachment%'
UNION ALL
SELECT
    'leave_request' as tabla,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'leave_request'
  AND column_name LIKE 'attachment%'
ORDER BY tabla, column_name;
