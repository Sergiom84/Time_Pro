#!/usr/bin/env python3
"""
Script para crear el cliente 'Patacones de mi tierra' en modo Lite
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar las funciones del script setup_client
from scripts.setup_client import create_client, create_admin_user

def main():
    print("=" * 70)
    print("CREANDO CLIENTE: PATACONES DE MI TIERRA (PLAN LITE)")
    print("=" * 70)
    print()

    # Datos del cliente
    client_name = "Patacones de mi tierra"
    plan = "lite"
    primary_color = "#0ea5e9"  # Color azul por defecto
    secondary_color = "#06b6d4"  # Color turquesa por defecto

    # Crear cliente
    print("📝 Creando cliente...")
    client = create_client(
        name=client_name,
        plan=plan,
        logo_path=None,  # Sin logo por ahora
        primary_color=primary_color,
        secondary_color=secondary_color
    )

    if not client:
        print("\n❌ Error al crear el cliente. Abortando.")
        return 1

    print()
    print("=" * 70)
    print("CREANDO USUARIO ADMINISTRADOR")
    print("=" * 70)
    print()

    # Datos del administrador
    admin_username = "admin_patacones"
    admin_password = "Patacones2025!"  # Cambiar en producción
    admin_full_name = "Administrador Patacones"
    admin_email = "admin@pataconesdetierra.com"

    # Crear admin
    admin = create_admin_user(
        client_id=client.id,
        username=admin_username,
        password=admin_password,
        full_name=admin_full_name,
        email=admin_email,
        client_slug=client.slug
    )

    if not admin:
        print("\n❌ Error al crear el usuario administrador.")
        return 1

    print()
    print("=" * 70)
    print("✅ ¡CLIENTE CREADO EXITOSAMENTE!")
    print("=" * 70)
    print()
    print(f"Cliente: {client.name}")
    print(f"Slug: {client.slug}")
    print(f"Plan: {client.plan.upper()}")
    print(f"ID: {client.id}")
    print()
    print("CREDENCIALES DEL ADMINISTRADOR:")
    print(f"Username: {admin.username}")
    print(f"Password: {admin_password}")
    print(f"Email: {admin.email}")
    print()
    print("💡 Guarda estas credenciales en un lugar seguro.")
    print("💡 El administrador puede ahora iniciar sesión en la aplicación.")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
