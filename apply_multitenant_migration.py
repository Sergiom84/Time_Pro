#!/usr/bin/env python3
"""
Script para aplicar la migración multi-tenant directamente a la BD.
No requiere todas las dependencias de Flask.
"""
import os
import sys
from urllib.parse import quote_plus

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 no está instalado. Instalando...")
    os.system("pip3 install -q psycopg2-binary")
    import psycopg2

# Obtener DATABASE_URL del entorno o usar la configuración por defecto
supabase_password = "OPt0u_oag6Pir5MR0@"
supabase_password_encoded = quote_plus(supabase_password)
default_dsn = (
    f"postgresql://postgres.gqesfclbingbihakiojm:"
    f"{supabase_password_encoded}@"
    f"aws-1-eu-west-1.pooler.supabase.com:6543/"
    f"postgres"
)

database_url = os.getenv("DATABASE_URL") or default_dsn
database_url = database_url.replace("postgres://", "postgresql://")

print("Conectando a la base de datos...")
print(f"URL: {database_url.replace(supabase_password, '****')}")

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(database_url)
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
        print("\n⚠️  La tabla 'client' ya existe. La migración ya fue aplicada.")
        print("Si necesitas volver a aplicarla, primero ejecuta el downgrade.")
        cursor.close()
        conn.close()
        sys.exit(0)

    # Paso 1: Crear enum para planes
    print("\n1. Creando enum plan_enum...")
    cursor.execute("CREATE TYPE plan_enum AS ENUM ('lite', 'pro')")
    print("   ✅ Enum creado")

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
    print("   ✅ Tabla client creada")

    # Paso 3: Crear cliente por defecto
    print("\n3. Creando cliente por defecto 'Time Pro'...")
    cursor.execute("""
        INSERT INTO client (id, name, slug, plan, is_active, primary_color, secondary_color, created_at)
        VALUES (1, 'Time Pro', 'timepro', 'pro', true, '#0ea5e9', '#06b6d4', NOW())
    """)
    print("   ✅ Cliente por defecto creado")

    # Paso 4: Agregar client_id a user
    print("\n4. Agregando columna client_id a tabla user...")
    cursor.execute('ALTER TABLE "user" ADD COLUMN client_id INTEGER')
    print("   ✅ Columna agregada")

    # Paso 5: Asignar usuarios existentes al cliente por defecto
    print("\n5. Asignando usuarios existentes al cliente por defecto...")
    cursor.execute('UPDATE "user" SET client_id = 1')
    rows_updated = cursor.rowcount
    print(f"   ✅ {rows_updated} usuarios actualizados")

    # Paso 6: Hacer client_id NOT NULL
    print("\n6. Haciendo client_id NOT NULL...")
    cursor.execute('ALTER TABLE "user" ALTER COLUMN client_id SET NOT NULL')
    print("   ✅ Constraint NOT NULL agregado")

    # Paso 7: Agregar foreign key
    print("\n7. Agregando foreign key user -> client...")
    cursor.execute("""
        ALTER TABLE "user"
        ADD CONSTRAINT fk_user_client_id
        FOREIGN KEY (client_id)
        REFERENCES client(id)
        ON DELETE CASCADE
    """)
    print("   ✅ Foreign key agregado")

    # Paso 8: Agregar client_id a system_config
    print("\n8. Agregando columna client_id a tabla system_config...")
    cursor.execute('ALTER TABLE system_config ADD COLUMN client_id INTEGER')
    print("   ✅ Columna agregada")

    # Paso 9: Asignar configuraciones existentes al cliente por defecto
    print("\n9. Asignando configuraciones existentes al cliente por defecto...")
    cursor.execute('UPDATE system_config SET client_id = 1')
    config_rows_updated = cursor.rowcount
    print(f"   ✅ {config_rows_updated} configuraciones actualizadas")

    # Paso 10: Hacer client_id NOT NULL
    print("\n10. Haciendo client_id NOT NULL en system_config...")
    cursor.execute('ALTER TABLE system_config ALTER COLUMN client_id SET NOT NULL')
    print("    ✅ Constraint NOT NULL agregado")

    # Paso 11: Agregar foreign key
    print("\n11. Agregando foreign key system_config -> client...")
    cursor.execute("""
        ALTER TABLE system_config
        ADD CONSTRAINT fk_system_config_client_id
        FOREIGN KEY (client_id)
        REFERENCES client(id)
        ON DELETE CASCADE
    """)
    print("    ✅ Foreign key agregado")

    # Paso 12: Eliminar constraint unique de key
    print("\n12. Eliminando constraint unique de key...")
    cursor.execute('ALTER TABLE system_config DROP CONSTRAINT IF EXISTS system_config_key_key')
    print("    ✅ Constraint eliminado")

    # Paso 13: Agregar constraint unique compuesto
    print("\n13. Agregando constraint unique compuesto (client_id, key)...")
    cursor.execute("""
        ALTER TABLE system_config
        ADD CONSTRAINT uix_client_key
        UNIQUE (client_id, key)
    """)
    print("    ✅ Constraint agregado")

    # Paso 14: Registrar migración en alembic_version
    print("\n14. Registrando migración en alembic_version...")
    cursor.execute("""
        INSERT INTO alembic_version (version_num)
        VALUES ('add_multitenant_001')
        ON CONFLICT (version_num) DO NOTHING
    """)
    print("    ✅ Migración registrada")

    # Commit de la transacción
    conn.commit()

    print("\n" + "="*60)
    print("✅ MIGRACIÓN APLICADA EXITOSAMENTE")
    print("="*60)
    print(f"\n📊 Resumen:")
    print(f"   - Tabla 'client' creada")
    print(f"   - {rows_updated} usuarios migrados")
    print(f"   - {config_rows_updated} configuraciones migradas")
    print(f"   - Cliente por defecto 'Time Pro' creado")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ Error al aplicar migración: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)
