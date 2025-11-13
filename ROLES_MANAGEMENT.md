# Gestión de Roles en Time Pro

## Descripción General

El sistema de Time Pro implementa un modelo de roles basado en el plan del cliente:

- **LITE**: Solo admins (1 admin por empresa, gestiona su centro)
- **PRO**: Admins + Super Admins (super admin gestiona todos los centros, admin gestiona su centro)

## Estructura de Roles en la Base de Datos

### Tabla: `user`

Campo: `role` (ENUM)
- `NULL` → Usuario normal (empleado)
- `'admin'` → Administrador de centro (solo PRO)
- `'super_admin'` → Super administrador (solo PRO)

### Migración Aplicada

Se ejecutó la migración `add_role_column_to_user.py` que:
1. Creó el tipo ENUM `role_enum` con valores `('admin', 'super_admin')`
2. Agregó la columna `role` a la tabla `user`
3. Migró datos antiguos: `is_admin=true` → `role='admin'`
4. Eliminó la columna obsoleta `is_admin`

## Gestión de Roles en Supabase (SQL Editor)

### Ver todos los usuarios y sus roles

```sql
SELECT id, username, full_name, role, center FROM "user"
ORDER BY role DESC NULLS LAST, username;
```

### Cambiar el rol de un usuario de empleado a admin

```sql
UPDATE "user"
SET role = 'admin'
WHERE id = <USER_ID>;
```

### Cambiar el rol de un usuario a super_admin

```sql
UPDATE "user"
SET role = 'super_admin'
WHERE id = <USER_ID>;
```

### Eliminar el rol de un usuario (convertirlo a empleado normal)

```sql
UPDATE "user"
SET role = NULL
WHERE id = <USER_ID>;
```

### Ver todos los admins y super admins

```sql
SELECT id, username, full_name, role, client_id
FROM "user"
WHERE role IS NOT NULL
ORDER BY role DESC, username;
```

### Ver super admins por cliente

```sql
SELECT u.id, u.username, u.full_name, c.name as client_name, u.role
FROM "user" u
JOIN "client" c ON u.client_id = c.id
WHERE u.role = 'super_admin'
ORDER BY c.name, u.username;
```

### Ver admins que gestionen un centro específico

```sql
SELECT id, username, full_name, centro
FROM "user"
WHERE role = 'admin' AND centro = 'Centro 1'
ORDER BY username;
```

## Restricciones por Plan

### Plan LITE

- **Máximo 1 admin** por empresa
- El admin es creado al registrar la empresa
- El admin gestiona un único centro
- **No permitido**: crear super_admin en LITE

### Plan PRO

- **Super admin**: Acceso global a todos los centros
- **Admins**: Cada uno gestiona su centro asignado
- **Empleados**: Sin permisos de administración
- Los super admins pueden crear/editar otros admins

## Interfaz Web vs Supabase

### Crear/Editar Roles (Recomendado)

**Usar la interfaz web** en `/admin/users` si es posible:
- Validaciones automáticas
- Respeta restricciones de plan
- Auditoría integrada

**Usar Supabase SQL Editor** solo cuando:
- Necesites hacer cambios masivos
- La interfaz no funcione
- Necesites migrar datos

## Validaciones de Seguridad

### Quién puede asignar roles

| Usuario | Plan | Puede crear Admin | Puede crear Super Admin |
|---------|------|-------------------|------------------------|
| Admin normal | PRO | ❌ No | ❌ No |
| Super Admin | PRO | ✅ Sí | ✅ Sí |
| Admin | LITE | ❌ No | ❌ No (no existe) |

### Validaciones automáticas

1. Solo super_admin en PRO puede conceder roles
2. Un super_admin debe tener `centro = '-- Sin categoría --'`
3. Un admin debe tener un centro específico asignado
4. En LITE no se permiten super_admin

## Ejemplos Prácticos

### Caso 1: Cambiar a un empleado a admin de Centro 1

```sql
UPDATE "user"
SET role = 'admin'
WHERE username = 'juan_smith' AND client_id = 1;
```

### Caso 2: Convertir un admin a super_admin

```sql
UPDATE "user"
SET role = 'super_admin', centro = '-- Sin categoría --'
WHERE id = 5;
```

### Caso 3: Revocar todos los permisos de un usuario

```sql
UPDATE "user"
SET role = NULL
WHERE id = 10;
```

## Troubleshooting

### Error: "No tienes permisos para crear super admin"

**Causa**: El usuario intenta crear un super_admin pero no es super_admin.
**Solución**: Solo un super_admin puede crear otros super_admin. Usa Supabase para promover el usuario primero.

### Un usuario con rol pero no ve opciones de admin

**Causa**: El usuario tiene `role='admin'` pero no tiene un centro asignado.
**Solución**:
```sql
UPDATE "user"
SET centro = 'Centro 1'
WHERE id = <USER_ID>;
```

### Super admin creado pero no ve todos los centros

**Causa**: El super_admin tiene un centro asignado (debería ser NULL).
**Solución**:
```sql
UPDATE "user"
SET centro = '-- Sin categoría --'
WHERE role = 'super_admin' AND id = <USER_ID>;
```

## Migraciones Futuras

Si necesitas:
- Cambiar restricciones de roles
- Agregar nuevos tipos de rol
- Modificar validaciones

Crea una nueva migración en `migrations/versions/`
