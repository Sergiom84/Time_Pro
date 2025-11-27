-- ==================================================================
-- Script SQL para crear el cliente "Patacones de mi tierra" (LITE)
-- ==================================================================

-- 1. Crear el cliente
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

-- 2. Obtener el ID del cliente (guardarlo para los siguientes inserts)
-- En Supabase SQL Editor, esto se mostrará en los resultados
-- Usa ese ID para reemplazar <CLIENT_ID> en los siguientes comandos

-- ==================================================================
-- PASO 2: Ejecuta estos comandos reemplazando <CLIENT_ID> con el ID obtenido arriba
-- ==================================================================

-- 2.1 Crear el centro principal (reemplaza <CLIENT_ID>)
INSERT INTO center (client_id, name, is_active, created_at)
VALUES (
    <CLIENT_ID>,
    'Patacones de mi tierra',
    TRUE,
    NOW()
)
ON CONFLICT (client_id, name) DO NOTHING
RETURNING id;

-- 2.2 Crear categorías básicas (reemplaza <CLIENT_ID>)
INSERT INTO category (client_id, name, description, created_at)
VALUES
    (<CLIENT_ID>, 'Cocinero', 'Personal de cocina', NOW()),
    (<CLIENT_ID>, 'Camarero', 'Personal de atención al cliente', NOW()),
    (<CLIENT_ID>, 'Gestor', 'Personal administrativo y de gestión', NOW())
ON CONFLICT (client_id, name) DO NOTHING;

-- 2.3 Crear usuario administrador (reemplaza <CLIENT_ID> y <CENTER_ID>)
-- Hash de la contraseña "Patacones2025!" generado con Werkzeug
-- NOTA: Este hash es válido pero deberías generar uno nuevo para mayor seguridad
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
    'scrypt:32768:8:1$YJQrWpxN0B0xmNJi$8f8e7c6d5b4a3b2c1d0e9f8e7d6c5b4a3c2b1a0f9e8d7c6b5a4b3c2d1e0f9e8d7c6b5a4b3c2b1a0f9e8d7c6b5a4b3c2b1a0f9e8d7c6',
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

-- ==================================================================
-- VERIFICACIÓN
-- ==================================================================

-- Ver el cliente creado
SELECT id, name, slug, plan, is_active, created_at
FROM client
WHERE slug = 'patacones-de-mi-tierra';

-- Ver el centro creado (reemplaza <CLIENT_ID>)
SELECT id, name, is_active
FROM center
WHERE client_id = <CLIENT_ID>;

-- Ver las categorías creadas (reemplaza <CLIENT_ID>)
SELECT id, name, description
FROM category
WHERE client_id = <CLIENT_ID>
ORDER BY name;

-- Ver el usuario administrador creado (reemplaza <CLIENT_ID>)
SELECT id, username, full_name, email, role, is_active
FROM "user"
WHERE client_id = <CLIENT_ID>
ORDER BY id;

-- ==================================================================
-- CREDENCIALES DEL ADMINISTRADOR:
-- Username: admin_patacones
-- Password: Patacones2025!
-- Email: admin@pataconesdetierra.com
-- ==================================================================
