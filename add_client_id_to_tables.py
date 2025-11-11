#!/usr/bin/env python3
"""
Script para agregar client_id a TimeRecord, WorkPause, LeaveRequest, EmployeeStatus.
"""
import os
import sys
from urllib.parse import quote_plus

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
    print("[ERROR] psycopg2 no está instalado. Instalando...")
    os.system("pip3 install -q psycopg2-binary")
    import psycopg2

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
    print("AGREGANDO CLIENT_ID A TABLAS")
    print("="*60)

    # TimeRecord
    print("\n1. Verificando columna client_id en time_record...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'time_record' AND column_name = 'client_id'
        );
    """)
    if cursor.fetchone()[0]:
        print("   [SKIP] client_id ya existe en time_record")
    else:
        print("   Agregando client_id a time_record...")
        cursor.execute("ALTER TABLE time_record ADD COLUMN client_id INTEGER")
        cursor.execute("UPDATE time_record SET client_id = 1")
        cursor.execute("ALTER TABLE time_record ALTER COLUMN client_id SET NOT NULL")
        cursor.execute("""
            ALTER TABLE time_record
            ADD CONSTRAINT fk_time_record_client_id
            FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE CASCADE
        """)
        cursor.execute("SELECT COUNT(*) FROM time_record")
        count = cursor.fetchone()[0]
        print(f"   [OK] {count} registros actualizados")

    # WorkPause
    print("\n2. Verificando columna client_id en work_pause...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'work_pause' AND column_name = 'client_id'
        );
    """)
    if cursor.fetchone()[0]:
        print("   [SKIP] client_id ya existe en work_pause")
    else:
        print("   Agregando client_id a work_pause...")
        cursor.execute("ALTER TABLE work_pause ADD COLUMN client_id INTEGER")
        cursor.execute("UPDATE work_pause SET client_id = 1")
        cursor.execute("ALTER TABLE work_pause ALTER COLUMN client_id SET NOT NULL")
        cursor.execute("""
            ALTER TABLE work_pause
            ADD CONSTRAINT fk_work_pause_client_id
            FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE CASCADE
        """)
        cursor.execute("SELECT COUNT(*) FROM work_pause")
        count = cursor.fetchone()[0]
        print(f"   [OK] {count} registros actualizados")

    # LeaveRequest
    print("\n3. Verificando columna client_id en leave_request...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'leave_request' AND column_name = 'client_id'
        );
    """)
    if cursor.fetchone()[0]:
        print("   [SKIP] client_id ya existe en leave_request")
    else:
        print("   Agregando client_id a leave_request...")
        cursor.execute("ALTER TABLE leave_request ADD COLUMN client_id INTEGER")
        cursor.execute("UPDATE leave_request SET client_id = 1")
        cursor.execute("ALTER TABLE leave_request ALTER COLUMN client_id SET NOT NULL")
        cursor.execute("""
            ALTER TABLE leave_request
            ADD CONSTRAINT fk_leave_request_client_id
            FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE CASCADE
        """)
        cursor.execute("SELECT COUNT(*) FROM leave_request")
        count = cursor.fetchone()[0]
        print(f"   [OK] {count} registros actualizados")

    # EmployeeStatus
    print("\n4. Verificando columna client_id en employee_status...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_name = 'employee_status' AND column_name = 'client_id'
        );
    """)
    if cursor.fetchone()[0]:
        print("   [SKIP] client_id ya existe en employee_status")
    else:
        print("   Agregando client_id a employee_status...")
        cursor.execute("ALTER TABLE employee_status ADD COLUMN client_id INTEGER")
        cursor.execute("UPDATE employee_status SET client_id = 1")
        cursor.execute("ALTER TABLE employee_status ALTER COLUMN client_id SET NOT NULL")
        cursor.execute("""
            ALTER TABLE employee_status
            ADD CONSTRAINT fk_employee_status_client_id
            FOREIGN KEY (client_id) REFERENCES client(id) ON DELETE CASCADE
        """)

        # Actualizar unique constraint
        print("   Actualizando constraint unique...")
        cursor.execute("ALTER TABLE employee_status DROP CONSTRAINT IF EXISTS uix_employee_date")
        cursor.execute("""
            ALTER TABLE employee_status
            ADD CONSTRAINT uix_employee_date
            UNIQUE (client_id, user_id, date)
        """)
        cursor.execute("SELECT COUNT(*) FROM employee_status")
        count = cursor.fetchone()[0]
        print(f"   [OK] {count} registros actualizados")

    # Commit
    conn.commit()

    print("\n" + "="*60)
    print("[OK] MIGRACION COMPLETADA EXITOSAMENTE")
    print("="*60)

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
