#!/usr/bin/env python3
"""
Script para aplicar la migración multi-tenant directamente a la BD.
No requiere todas las dependencias de Flask.
"""
import os
import sys
from urllib.parse import quote_plus

# Fix IPv4 para conexiones Supabase (igual que en main.py)
import socket
_original_getaddrinfo = socket.getaddrinfo
def _force_ipv4(*args, **kwargs):
    host = args[0] if args else kwargs.get('host', '')
    if 'pooler.supabase.com' in str(host) or ('supabase.co' in str(host) and 'db.' in str(host)):
        kwargs['family'] = socket.AF_INET
    return _original_getaddrinfo(*args, **kwargs)
socket.getaddrinfo = _force_ipv4

try:
    import psycopg2
except ImportError:
    print("[ERROR] psycopg2 no está instalado. Instalando...")
    os.system("pip3 install -q psycopg2-binary")
    import psycopg2

# Obtener DATABASE_URL del entorno (obligatorio)
# NO usar credenciales hardcodeadas por seguridad
from dotenv import load_dotenv
load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("[ERROR] ERROR: DATABASE_URL no está configurada en .env")
    print("Por favor, configura DATABASE_URL en tu archivo .env")
    sys.exit(1)
database_url = database_url.replace("postgres://", "postgresql://")

print("Conectando a la base de datos...")
# Ocultar contraseña en la salida
from urllib.parse import urlparse
parsed = urlparse(database_url)
safe_url = database_url.replace(parsed.password, '****') if parsed.password else database_url
print(f"URL: {safe_url}")

try:
    # Conectar a la base de datos con SSL requerido
    conn = psycopg2.connect(database_url, sslmode='require', connect_timeout=15)
    conn.autocommit = False
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("APLICANDO MIGRACIÓN MULTI-TENANT")
    print("="*60)

    # Verificar si la tabla client ya existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'client'
        );
    """)
    client_table_exists = cursor.fetchone()[0]

    if client_table_exists:
        print("\n[WARN]  La tabla 'client' ya existe. La migración ya fue aplicada.")
        print("Si necesitas volver a aplicarla, primero ejecuta el downgrade.")
        cursor.close()
        conn.close()
        sys.exit(0)

    # Paso 1: Crear enum para planes
    print("\n1. Creando enum plan_enum...")
    cursor.execute("CREATE TYPE plan_enum AS ENUM ('lite', 'pro')")
    print("   [OK] Enum creado")

    # Paso 2: Crear tabla client
    print("\n2. Creando tabla client...")
    cursor.execute("""
        CREATE TABLE client (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) UNIQUE NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            plan plan_enum NOT NULL DEFAULT 'pro',
            logo_url VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT true,
            primary_color VARCHAR(7) DEFAULT '#0ea5e9',
            secondary_color VARCHAR(7) DEFAULT '#06b6d4',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("   [OK] Tabla client creada")

    # Paso 3: Crear cliente por defecto
    print("\n3. Creando cliente por defecto 'Time Pro'...")
    cursor.execute("""
        INSERT INTO client (id, name, slug, plan, is_active, primary_color, secondary_color, created_at)
        VALUES (1, 'Time Pro', 'timepro', 'pro', true, '#0ea5e9', '#06b6d4', NOW())
    """)
    print("   [OK] Cliente por defecto creado")

    # Paso 4: Agregar client_id a user (si no existe)
    print("\n4. Verificando columna client_id en tabla user...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'user' AND column_name = 'client_id'
        );
    """)
    user_client_id_exists = cursor.fetchone()[0]

    if user_client_id_exists:
        print("   [SKIP] La columna client_id ya existe en user")
    else:
        cursor.execute('ALTER TABLE "user" ADD COLUMN client_id INTEGER')
        print("   [OK] Columna client_id agregada a user")

    # Paso 5: Asignar usuarios existentes al cliente por defecto
    print("\n5. Asignando usuarios existentes al cliente por defecto...")
    cursor.execute('UPDATE "user" SET client_id = 1')
    rows_updated = cursor.rowcount
    print(f"   [OK] {rows_updated} usuarios actualizados")

    # Paso 6: Hacer client_id NOT NULL (si no lo es ya)
    print("\n6. Verificando constraint NOT NULL en user.client_id...")
    cursor.execute("""
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'client_id';
    """)
    result = cursor.fetchone()
    is_nullable = result[0] if result else 'YES'

    if is_nullable == 'NO':
        print("   [SKIP] client_id ya es NOT NULL")
    else:
        cursor.execute('ALTER TABLE "user" ALTER COLUMN client_id SET NOT NULL')
        print("   [OK] Constraint NOT NULL agregado")

    # Paso 7: Agregar foreign key (si no existe)
    print("\n7. Verificando foreign key user -> client...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_user_client_id'
            AND table_name = 'user'
        );
    """)
    fk_user_exists = cursor.fetchone()[0]

    if fk_user_exists:
        print("   [SKIP] Foreign key fk_user_client_id ya existe")
    else:
        cursor.execute("""
            ALTER TABLE "user"
            ADD CONSTRAINT fk_user_client_id
            FOREIGN KEY (client_id)
            REFERENCES client(id)
            ON DELETE CASCADE
        """)
        print("   [OK] Foreign key agregado")

    # Paso 8: Agregar client_id a system_config (si no existe)
    print("\n8. Verificando columna client_id en tabla system_config...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'system_config' AND column_name = 'client_id'
        );
    """)
    config_client_id_exists = cursor.fetchone()[0]

    if config_client_id_exists:
        print("   [SKIP] La columna client_id ya existe en system_config")
    else:
        cursor.execute('ALTER TABLE system_config ADD COLUMN client_id INTEGER')
        print("   [OK] Columna client_id agregada a system_config")

    # Paso 9: Asignar configuraciones existentes al cliente por defecto
    print("\n9. Asignando configuraciones existentes al cliente por defecto...")
    cursor.execute('UPDATE system_config SET client_id = 1')
    config_rows_updated = cursor.rowcount
    print(f"   [OK] {config_rows_updated} configuraciones actualizadas")

    # Paso 10: Hacer client_id NOT NULL (si no lo es ya)
    print("\n10. Verificando constraint NOT NULL en system_config.client_id...")
    cursor.execute("""
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_name = 'system_config' AND column_name = 'client_id';
    """)
    result = cursor.fetchone()
    is_nullable = result[0] if result else 'YES'

    if is_nullable == 'NO':
        print("    [SKIP] client_id ya es NOT NULL")
    else:
        cursor.execute('ALTER TABLE system_config ALTER COLUMN client_id SET NOT NULL')
        print("    [OK] Constraint NOT NULL agregado")

    # Paso 11: Agregar foreign key (si no existe)
    print("\n11. Verificando foreign key system_config -> client...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_system_config_client_id'
            AND table_name = 'system_config'
        );
    """)
    fk_config_exists = cursor.fetchone()[0]

    if fk_config_exists:
        print("    [SKIP] Foreign key fk_system_config_client_id ya existe")
    else:
        cursor.execute("""
            ALTER TABLE system_config
            ADD CONSTRAINT fk_system_config_client_id
            FOREIGN KEY (client_id)
            REFERENCES client(id)
            ON DELETE CASCADE
        """)
        print("    [OK] Foreign key agregado")

    # Paso 12: Eliminar constraint unique de key
    print("\n12. Eliminando constraint unique de key...")
    cursor.execute('ALTER TABLE system_config DROP CONSTRAINT IF EXISTS system_config_key_key')
    print("    [OK] Constraint eliminado")

    # Paso 13: Agregar constraint unique compuesto (si no existe)
    print("\n13. Verificando constraint unique compuesto (client_id, key)...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_name = 'uix_client_key'
            AND table_name = 'system_config'
        );
    """)
    uix_exists = cursor.fetchone()[0]

    if uix_exists:
        print("    [SKIP] Constraint uix_client_key ya existe")
    else:
        cursor.execute("""
            ALTER TABLE system_config
            ADD CONSTRAINT uix_client_key
            UNIQUE (client_id, key)
        """)
        print("    [OK] Constraint agregado")

    # Paso 14: Registrar migración en alembic_version
    print("\n14. Registrando migración en alembic_version...")
    cursor.execute("""
        INSERT INTO alembic_version (version_num)
        VALUES ('add_multitenant_001')
        ON CONFLICT (version_num) DO NOTHING
    """)
    print("    [OK] Migración registrada")

    # Commit de la transacción
    conn.commit()

    print("\n" + "="*60)
    print("[OK] MIGRACIÓN APLICADA EXITOSAMENTE")
    print("="*60)
    print(f"\n[INFO] Resumen:")
    print(f"   - Tabla 'client' creada")
    print(f"   - {rows_updated} usuarios migrados")
    print(f"   - {config_rows_updated} configuraciones migradas")
    print(f"   - Cliente por defecto 'Time Pro' creado")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n[ERROR] Error al aplicar migración: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)
