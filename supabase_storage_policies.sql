-- ========================================
-- Políticas de Storage para bucket 'Justificantes'
-- Time Pro - Sistema de gestión de tiempo
-- ========================================

-- IMPORTANTE: Ejecuta este script en la sección SQL Editor de tu Dashboard de Supabase
-- Ubicación: Dashboard > SQL Editor > New Query

-- ========================================
-- 1. ELIMINAR POLÍTICAS EXISTENTES (si las hay)
-- ========================================

DROP POLICY IF EXISTS "Usuarios autenticados pueden subir archivos" ON storage.objects;
DROP POLICY IF EXISTS "Usuarios autenticados pueden ver archivos" ON storage.objects;
DROP POLICY IF EXISTS "Usuarios autenticados pueden actualizar archivos" ON storage.objects;
DROP POLICY IF EXISTS "Usuarios autenticados pueden eliminar archivos" ON storage.objects;

-- ========================================
-- 2. POLÍTICA DE SUBIDA (INSERT)
-- ========================================
-- Permite a usuarios autenticados subir archivos al bucket 'Justificantes'

CREATE POLICY "Usuarios autenticados pueden subir archivos"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'Justificantes'
);

-- ========================================
-- 3. POLÍTICA DE LECTURA (SELECT)
-- ========================================
-- Permite a usuarios autenticados ver/descargar archivos del bucket 'Justificantes'

CREATE POLICY "Usuarios autenticados pueden ver archivos"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'Justificantes'
);

-- ========================================
-- 4. POLÍTICA DE ACTUALIZACIÓN (UPDATE)
-- ========================================
-- Permite a usuarios autenticados actualizar metadatos de archivos

CREATE POLICY "Usuarios autenticados pueden actualizar archivos"
ON storage.objects
FOR UPDATE
TO authenticated
USING (
  bucket_id = 'Justificantes'
)
WITH CHECK (
  bucket_id = 'Justificantes'
);

-- ========================================
-- 5. POLÍTICA DE ELIMINACIÓN (DELETE)
-- ========================================
-- Permite a usuarios autenticados eliminar archivos del bucket 'Justificantes'

CREATE POLICY "Usuarios autenticados pueden eliminar archivos"
ON storage.objects
FOR DELETE
TO authenticated
USING (
  bucket_id = 'Justificantes'
);

-- ========================================
-- VERIFICACIÓN
-- ========================================
-- Consulta para verificar que las políticas se crearon correctamente

SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename = 'objects'
  AND schemaname = 'storage'
  AND policyname LIKE '%Usuarios autenticados%'
ORDER BY policyname;

-- ========================================
-- RESULTADO ESPERADO
-- ========================================
-- Deberías ver 4 políticas:
-- 1. Usuarios autenticados pueden subir archivos (INSERT)
-- 2. Usuarios autenticados pueden ver archivos (SELECT)
-- 3. Usuarios autenticados pueden actualizar archivos (UPDATE)
-- 4. Usuarios autenticados pueden eliminar archivos (DELETE)

-- ========================================
-- NOTAS IMPORTANTES
-- ========================================
--
-- SEGURIDAD ACTUAL:
-- - Cualquier usuario AUTENTICADO puede subir, ver, actualizar y eliminar archivos
-- - Los archivos NO son públicos (requieren autenticación)
-- - La aplicación debe manejar la lógica de negocio para restringir acceso
--
-- MEJORAS FUTURAS (Opcional):
-- Si necesitas políticas más restrictivas donde cada usuario solo pueda
-- acceder a sus propios archivos, necesitarías:
--
-- 1. Almacenar metadata en los archivos con el user_id
-- 2. Crear políticas que comparen auth.uid() con la metadata
-- 3. Modificar el código de la aplicación para incluir metadata al subir archivos
--
-- Ejemplo de política más restrictiva (NO ejecutes esto aún):
-- CREATE POLICY "Usuarios solo ven sus archivos"
-- ON storage.objects FOR SELECT TO authenticated
-- USING (
--   bucket_id = 'Justificantes'
--   AND (storage.foldername(name))[1] = auth.uid()::text
-- );
--
-- Esto requeriría organizar archivos en carpetas por user_id
-- ========================================
