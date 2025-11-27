# Configuración del Cliente "Patacones de mi tierra"

Este documento describe cómo crear el nuevo cliente "Patacones de mi tierra" en modo LITE.

## Opción 1: Usar el Script Python (Recomendado)

Si tienes Python instalado con las dependencias de Flask:

### Paso 1: Ejecutar el script de configuración

Abre una terminal (PowerShell, CMD o WSL) y ejecuta:

```bash
python scripts/setup_client.py
```

Sigue las instrucciones e introduce los siguientes datos:

- **Nombre del cliente**: `Patacones de mi tierra`
- **Plan**: `lite`
- **Ruta al logo**: (presiona Enter para omitir)
- **Color principal**: (presiona Enter para usar default)
- **Color secundario**: (presiona Enter para usar default)

Para el administrador:

- **Username**: `admin_patacones`
- **Contraseña**: `Patacones2025!` (o la que prefieras)
- **Nombre completo**: `Administrador Patacones`
- **Email**: `admin@pataconesdetierra.com`

### Paso 2: Crear empleados adicionales

Una vez creado el cliente y el administrador, puedes crear empleados usando el panel de administración de la aplicación.

---

## Opción 2: Usar SQL directamente en Supabase

Si prefieres crear el cliente directamente en la base de datos:

### Paso 1: Generar el hash de contraseña

Ejecuta el siguiente comando para generar el hash de la contraseña del administrador:

```bash
python generate_password_hash.py
```

Cuando te pida la contraseña, introduce: `Patacones2025!`

Copia el hash generado.

### Paso 2: Ejecutar el SQL en Supabase

1. Ve al **SQL Editor** de Supabase: https://supabase.com/dashboard/project/gqesfclbingbihakiojm/sql

2. **Primera consulta**: Crear el cliente

```sql
INSERT INTO client (name, slug, plan, is_active, primary_color, secondary_color, created_at, updated_at)
VALUES (
    'Patacones de mi tierra',
    'patacones-de-mi-tierra',
    'lite',
    TRUE,
    '#0ea5e9',
    '#06b6d4',
    NOW(),
    NOW()
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    plan = EXCLUDED.plan,
    is_active = EXCLUDED.is_active,
    updated_at = NOW()
RETURNING id;
```

**IMPORTANTE**: Anota el ID que devuelve esta consulta (ej: 5). Lo necesitarás para los siguientes pasos.

3. **Segunda consulta**: Crear el centro (reemplaza `<CLIENT_ID>` con el ID del paso anterior)

```sql
INSERT INTO center (client_id, name, is_active, created_at)
VALUES (
    <CLIENT_ID>,
    'Patacones de mi tierra',
    TRUE,
    NOW()
)
ON CONFLICT (client_id, name) DO NOTHING
RETURNING id;
```

**IMPORTANTE**: Anota el ID del centro que devuelve esta consulta.

4. **Tercera consulta**: Crear categorías (reemplaza `<CLIENT_ID>`)

```sql
INSERT INTO category (client_id, name, description, created_at)
VALUES
    (<CLIENT_ID>, 'Cocinero', 'Personal de cocina', NOW()),
    (<CLIENT_ID>, 'Camarero', 'Personal de atención al cliente', NOW()),
    (<CLIENT_ID>, 'Gestor', 'Personal administrativo y de gestión', NOW())
ON CONFLICT (client_id, name) DO NOTHING;
```

5. **Cuarta consulta**: Crear el administrador (reemplaza `<CLIENT_ID>`, `<CENTER_ID>` y `<PASSWORD_HASH>`)

```sql
INSERT INTO "user" (
    client_id,
    username,
    password_hash,
    full_name,
    email,
    role,
    is_active,
    weekly_hours,
    center_id,
    theme_preference,
    created_at
)
VALUES (
    <CLIENT_ID>,
    'admin_patacones',
    '<PASSWORD_HASH>',
    'Administrador Patacones',
    'admin@pataconesdetierra.com',
    'super_admin',
    TRUE,
    40,
    <CENTER_ID>,
    'dark-turquoise',
    NOW()
)
ON CONFLICT (client_id, username) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    role = EXCLUDED.role
RETURNING id, username, email;
```

### Paso 3: Verificar la creación

Ejecuta esta consulta para verificar que todo se creó correctamente:

```sql
SELECT
    c.id as client_id,
    c.name as client_name,
    c.plan,
    u.id as user_id,
    u.username,
    u.email,
    u.role,
    ct.name as center_name
FROM client c
LEFT JOIN "user" u ON u.client_id = c.id
LEFT JOIN center ct ON ct.id = u.center_id
WHERE c.slug = 'patacones-de-mi-tierra';
```

---

## Opción 3: Usar el script create_patacones_client.py

Si tienes Python con Flask instalado, puedes usar el script automatizado:

```bash
python create_patacones_client.py
```

Este script creará automáticamente:
- El cliente con plan LITE
- El centro principal
- Las categorías básicas
- El administrador

---

## Credenciales del Administrador

Una vez completado cualquiera de los métodos anteriores:

- **URL de acceso**: http://localhost:5000 (o la URL de tu despliegue)
- **Username**: `admin_patacones`
- **Password**: `Patacones2025!`
- **Email**: `admin@pataconesdetierra.com`

---

## Próximos Pasos

### 1. Crear empleados

Inicia sesión como administrador y ve a:
- **Panel de Control** → **Gestionar Empleados** → **Añadir Empleado**

Recuerda que en el plan LITE tienes un máximo de **5 empleados**.

### 2. Configurar categorías y centros

Si necesitas categorías adicionales o modificar el centro:
- Ve a **Configuración** en el panel de administración

### 3. Probar el sistema

1. Crea algunos empleados de prueba
2. Prueba el sistema de fichajes
3. Verifica que las restricciones del plan LITE funcionen correctamente

---

## Características del Plan LITE

✅ **Incluye**:
- Hasta 5 empleados
- 1 centro
- Fichajes básicos
- Reportes básicos
- Exportación a Excel
- Vista de calendario
- Solicitudes de permisos
- Pausas de trabajo
- Notificaciones por email

❌ **No incluye**:
- Empleados ilimitados
- Múltiples centros
- Reportes avanzados
- Funciones multi-centro

---

## Soporte

Si encuentras algún problema durante la configuración, verifica:

1. Que la base de datos esté accesible
2. Que las variables de entorno en `.env` estén configuradas correctamente
3. Que el plan del cliente sea `lite` en la base de datos

Para más ayuda, contacta al equipo de desarrollo.
