#!/usr/bin/env python3
"""
Script para cambiar constraints unique de username y email a compuestos (client_id, username) y (client_id, email).
"""
import os
import sys

# Fix IPv4 para conexiones Supabase
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
    print("[ERROR] psycopg2 no está instalado.")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("[ERROR] DATABASE_URL no está configurada en .env")
    sys.exit(1)
database_url = database_url.replace("postgres://", "postgresql://")

print("Conectando a la base de datos...")
from urllib.parse import urlparse
parsed = urlparse(database_url)
safe_url = database_url.replace(parsed.password, '****') if parsed.password else database_url
print(f"URL: {safe_url}")

try:
    conn = psycopg2.connect(database_url, sslmode='require', connect_timeout=15)
    conn.autocommit = False
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("ACTUALIZANDO CONSTRAINTS DE USER")
    print("="*60)

    # Eliminar constraint unique de username
    print("\n1. Eliminando constraint unique de username...")
    cursor.execute('ALTER TABLE "user" DROP CONSTRAINT IF EXISTS user_username_key')
    print("   [OK] Constraint eliminado")

    # Eliminar constraint unique de email
    print("\n2. Eliminando constraint unique de email...")
    cursor.execute('ALTER TABLE "user" DROP CONSTRAINT IF EXISTS user_email_key')
    print("   [OK] Constraint eliminado")

    # Agregar constraint unique compuesto (client_id, username)
    print("\n3. Agregando constraint unique compuesto (client_id, username)...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_name = 'uix_client_username'
            AND table_name = 'user'
        );
    """)
    if cursor.fetchone()[0]:
        print("   [SKIP] Constraint uix_client_username ya existe")
    else:
        cursor.execute("""
            ALTER TABLE "user"
            ADD CONSTRAINT uix_client_username
            UNIQUE (client_id, username)
        """)
        print("   [OK] Constraint agregado")

    # Agregar constraint unique compuesto (client_id, email)
    print("\n4. Agregando constraint unique compuesto (client_id, email)...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints
            WHERE constraint_name = 'uix_client_email'
            AND table_name = 'user'
        );
    """)
    if cursor.fetchone()[0]:
        print("   [SKIP] Constraint uix_client_email ya existe")
    else:
        cursor.execute("""
            ALTER TABLE "user"
            ADD CONSTRAINT uix_client_email
            UNIQUE (client_id, email)
        """)
        print("   [OK] Constraint agregado")

    # Commit
    conn.commit()

    print("\n" + "="*60)
    print("[OK] CONSTRAINTS ACTUALIZADOS EXITOSAMENTE")
    print("="*60)
    print("\n[INFO] Ahora username y email son unicos por cliente, no globalmente.")

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
