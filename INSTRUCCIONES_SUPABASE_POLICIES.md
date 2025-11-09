# Instrucciones para configurar políticas de Storage en Supabase

## Paso 1: Acceder al SQL Editor

1. Ve a tu Dashboard de Supabase: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. En el menú lateral izquierdo, haz clic en **SQL Editor**
4. Haz clic en **New query** (o el botón **+** para crear una nueva consulta)

## Paso 2: Ejecutar el script SQL

1. Abre el archivo `supabase_storage_policies.sql` que se acaba de crear
2. Copia TODO el contenido del archivo
3. Pégalo en el editor SQL de Supabase
4. Haz clic en el botón **Run** (o presiona `Ctrl + Enter` / `Cmd + Enter`)

## Paso 3: Verificar que las políticas se crearon correctamente

Después de ejecutar el script, verás un resultado similar a este:

```
4 políticas creadas correctamente:
✓ Usuarios autenticados pueden subir archivos
✓ Usuarios autenticados pueden ver archivos
✓ Usuarios autenticados pueden actualizar archivos
✓ Usuarios autenticados pueden eliminar archivos
```

## Paso 4: Verificar visualmente en el Dashboard

1. Ve a **Storage** en el menú lateral
2. Haz clic en el bucket **Justificantes**
3. Haz clic en la pestaña **Policies**
4. Deberías ver las 4 políticas listadas

## ¿Qué hacen estas políticas?

### Nivel de seguridad ACTUAL:
- ✓ Solo usuarios **autenticados** pueden acceder a los archivos
- ✓ Los archivos NO son públicos
- ✓ Requiere login en la aplicación para subir/ver archivos
- ✓ Cualquier usuario autenticado puede ver todos los archivos del bucket

### Si necesitas más restricciones en el futuro:

Si quieres que cada usuario solo pueda ver **sus propios archivos**, necesitarás:
1. Modificar el código de la aplicación para organizar archivos en carpetas por usuario
2. Crear políticas más específicas basadas en la estructura de carpetas
3. Avisar para implementar esta mejora

## Solución de problemas

### Error: "permission denied for table objects"
- Asegúrate de estar usando la cuenta correcta de Supabase
- Verifica que tienes permisos de administrador en el proyecto

### Error: "policy already exists"
- El script ya incluye `DROP POLICY IF EXISTS` para eliminar políticas existentes
- Si persiste, elimina las políticas manualmente desde Storage > Policies

### Las políticas no aparecen
- Refresca la página del Dashboard
- Verifica que ejecutaste el script completo (no solo parte)
- Revisa la sección de errores en el SQL Editor

## Siguiente paso

Después de ejecutar este script, tu aplicación podrá:
- Subir archivos a Supabase Storage
- Descargar archivos desde Supabase Storage
- Eliminar archivos cuando sea necesario

Para probar que todo funciona, puedes ejecutar el script `test_bucket_access.py` nuevamente.
