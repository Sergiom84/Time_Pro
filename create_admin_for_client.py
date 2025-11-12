#!/usr/bin/env python3
"""
Script para crear un administrador para un cliente existente
Uso: python create_admin_for_client.py
"""
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL') or "https://gqesfclbingbihakiojm.supabase.co"
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxZXNmY2xiaW5nYmloYWtpb2ptIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTgyNzY3MSwiZXhwIjoyMDc3NDAzNjcxfQ.GjRCAqnuuTvUObVf8i9cl5bYCxBKS2EWUncIQIB5kyM"

def create_admin_interactive():
    """Crear administrador de forma interactiva"""
    print("=" * 60)
    print("    CREAR ADMINISTRADOR PARA CLIENTE EXISTENTE")
    print("=" * 60)
    print()

    # Conectar a Supabase
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Listar clientes disponibles
    print("📋 CLIENTES DISPONIBLES:")
    print("-" * 60)
    try:
        response = client.table('client').select('*').order('id').execute()

        if not response.data:
            print("❌ No hay clientes en la base de datos")
            return

        for c in response.data:
            status = "✅ Activo" if c.get('is_active') else "❌ Inactivo"
            print(f"  ID: {c['id']} | {c['name']} ({c['plan'].upper()}) | {status}")
            print(f"       Slug: {c['slug']}")
            print()

    except Exception as e:
        print(f"❌ Error al obtener clientes: {e}")
        return

    print("-" * 60)

    # Solicitar ID del cliente
    while True:
        client_id_input = input("\n🔢 ID del cliente para el que crear admin: ").strip()

        if not client_id_input.isdigit():
            print("❌ El ID debe ser un número")
            continue

        client_id = int(client_id_input)

        # Verificar que el cliente existe
        try:
            client_data = client.table('client').select('*').eq('id', client_id).execute()

            if not client_data.data:
                print(f"❌ No existe un cliente con ID {client_id}")
                continue

            selected_client = client_data.data[0]
            print(f"\n✅ Cliente seleccionado: {selected_client['name']} ({selected_client['plan'].upper()})")
            break

        except Exception as e:
            print(f"❌ Error al verificar cliente: {e}")
            return

    print("\n" + "=" * 60)
    print("    DATOS DEL ADMINISTRADOR")
    print("=" * 60)

    # Solicitar datos del admin
    username = input("\n👤 Username: ").strip()
    if not username:
        print("❌ El username no puede estar vacío")
        return

    # Verificar que el username no existe para este cliente
    try:
        existing = client.table('user').select('id').eq('client_id', client_id).eq('username', username).execute()
        if existing.data:
            print(f"❌ Ya existe un usuario '{username}' para este cliente")
            return
    except Exception as e:
        print(f"❌ Error al verificar username: {e}")
        return

    full_name = input("📛 Nombre completo: ").strip()
    if not full_name:
        print("❌ El nombre completo no puede estar vacío")
        return

    email = input("📧 Email: ").strip()
    if not email:
        print("❌ El email no puede estar vacío")
        return

    # Verificar que el email no existe para este cliente
    try:
        existing_email = client.table('user').select('id').eq('client_id', client_id).eq('email', email).execute()
        if existing_email.data:
            print(f"❌ Ya existe un usuario con email '{email}' para este cliente")
            return
    except Exception as e:
        print(f"❌ Error al verificar email: {e}")
        return

    password = input("🔒 Contraseña: ").strip()
    if not password:
        print("❌ La contraseña no puede estar vacía")
        return

    password_confirm = input("🔒 Confirmar contraseña: ").strip()
    if password != password_confirm:
        print("❌ Las contraseñas no coinciden")
        return

    # Centro (opcional)
    print("\n🏢 Centro (opcional):")
    print("  1. -- Sin categoría --")
    print("  2. Centro 1")
    print("  3. Centro 2")
    print("  4. Centro 3")
    centro_option = input("Seleccionar (Enter para sin categoría): ").strip()

    centro_map = {
        "1": "-- Sin categoría --",
        "2": "Centro 1",
        "3": "Centro 2",
        "4": "Centro 3",
        "": "-- Sin categoría --"
    }
    centro = centro_map.get(centro_option, "-- Sin categoría --")

    # Categoría
    print("\n👔 Categoría:")
    print("  1. Coordinador")
    print("  2. Empleado")
    print("  3. Gestor")
    categoria_option = input("Seleccionar [3]: ").strip() or "3"

    categoria_map = {
        "1": "Coordinador",
        "2": "Empleado",
        "3": "Gestor"
    }
    categoria = categoria_map.get(categoria_option, "Gestor")

    print("\n" + "=" * 60)
    print("    CONFIRMACIÓN")
    print("=" * 60)
    print(f"Cliente: {selected_client['name']} (ID: {client_id})")
    print(f"Username: {username}")
    print(f"Nombre: {full_name}")
    print(f"Email: {email}")
    print(f"Centro: {centro}")
    print(f"Categoría: {categoria}")
    print(f"Admin: SÍ")
    print("=" * 60)

    confirm = input("\n¿Crear este administrador? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Operación cancelada")
        return

    # Generar hash de contraseña
    print("\n🔐 Generando hash de contraseña...")
    password_hash = generate_password_hash(password)

    # Crear usuario en Supabase
    print("💾 Creando usuario en base de datos...")
    try:
        new_user = {
            'client_id': client_id,
            'username': username,
            'password_hash': password_hash,
            'full_name': full_name,
            'email': email,
            'is_admin': True,
            'is_active': True,
            'weekly_hours': 40,
            'centro': centro,
            'categoria': categoria,
            'theme_preference': 'dark-turquoise'
        }

        response = client.table('user').insert(new_user).execute()

        if response.data:
            created_user = response.data[0]
            print("\n" + "=" * 60)
            print("    ✅ ADMINISTRADOR CREADO EXITOSAMENTE")
            print("=" * 60)
            print(f"ID: {created_user['id']}")
            print(f"Cliente: {selected_client['name']}")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Centro: {centro}")
            print(f"Categoría: {categoria}")
            print("\n💡 El administrador ya puede iniciar sesión en la aplicación.")
            print(f"   URL de login: https://time-pro-1dj0.onrender.com/login")
            print(f"   Identificador de empresa: {selected_client['slug']} (o {client_id})")
            print("=" * 60)
        else:
            print("❌ Error: No se pudo crear el usuario")

    except Exception as e:
        print(f"\n❌ Error al crear usuario: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        create_admin_interactive()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
