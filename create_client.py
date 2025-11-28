#!/usr/bin/env python3
"""
Script simplificado para crear un nuevo cliente en Time Pro.
Solicita solo los datos esenciales: nombre, plan, centro y credenciales del admin.
NO solicita logo ni colores (usa defaults).

Uso: python create_client.py
"""
import sys
from pathlib import Path
from getpass import getpass

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client, User, Center
from main import app

# Importar funciones reutilizables del script original
from scripts.setup_client import (
    create_client,
    create_admin_user,
    slugify,
    _generate_placeholder_email
)


def crear_centro_inicial(client_id, nombre_centro):
    """
    Crea el centro inicial para el cliente.

    Args:
        client_id: ID del cliente
        nombre_centro: Nombre del centro (ej: "Sede Principal")

    Returns:
        Objeto Center creado o None si hay error
    """
    with app.app_context():
        try:
            # Verificar que no exista
            existing = Center.query.filter_by(
                client_id=client_id,
                name=nombre_centro
            ).first()

            if existing:
                print(f"ℹ️  El centro '{nombre_centro}' ya existe para este cliente")
                return existing

            # Crear centro
            center = Center(
                client_id=client_id,
                name=nombre_centro,
                is_active=True
            )

            db.session.add(center)
            db.session.commit()

            print(f"✅ Centro '{nombre_centro}' creado exitosamente")
            print(f"   ID: {center.id}")

            return center

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear centro: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """
    Flujo interactivo simplificado para crear un nuevo cliente.
    """
    print("=" * 70)
    print("             TIME PRO - CREAR NUEVO CLIENTE")
    print("=" * 70)
    print()
    print("Este script creará:")
    print("  • Un nuevo cliente (empresa)")
    print("  • Un centro inicial")
    print("  • Un usuario administrador")
    print()
    print("-" * 70)
    print()

    # 1. DATOS DEL CLIENTE
    print("📋 DATOS DEL CLIENTE")
    print("-" * 70)

    nombre_empresa = input("Nombre de la empresa: ").strip()
    if not nombre_empresa:
        print("❌ El nombre de la empresa es obligatorio")
        return 1

    # Validar plan
    while True:
        plan = input("Plan (lite/pro) [lite]: ").strip().lower() or "lite"
        if plan in ['lite', 'pro']:
            break
        print("❌ Plan inválido. Debe ser 'lite' o 'pro'")

    print()

    # 2. DATOS DEL CENTRO
    print("🏢 CENTRO INICIAL")
    print("-" * 70)

    nombre_centro = input("Nombre del centro (ej: Sede Principal, Madrid Centro): ").strip()
    if not nombre_centro:
        print("❌ El nombre del centro es obligatorio")
        return 1

    print()

    # 3. DATOS DEL ADMINISTRADOR
    print("👤 ADMINISTRADOR")
    print("-" * 70)

    username = input("Username del administrador: ").strip()
    if not username:
        print("❌ El username es obligatorio")
        return 1

    # Solicitar contraseña con confirmación
    while True:
        password = getpass("Contraseña: ")
        if not password:
            print("❌ La contraseña es obligatoria")
            continue

        password_confirm = getpass("Confirmar contraseña: ")
        if password != password_confirm:
            print("❌ Las contraseñas no coinciden. Intenta de nuevo.")
            continue

        break

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Empresa: {nombre_empresa}")
    print(f"Plan: {plan.upper()}")
    print(f"Centro: {nombre_centro}")
    print(f"Admin: {username}")
    print()

    # Confirmar
    confirmar = input("¿Proceder con la creación? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Operación cancelada")
        return 1

    print()
    print("=" * 70)
    print("CREANDO...")
    print("=" * 70)
    print()

    # 4. CREAR CLIENTE
    print("1️⃣  Creando cliente...")
    client = create_client(
        name=nombre_empresa,
        plan=plan,
        logo_path=None,  # Sin logo
        primary_color="#0ea5e9",  # Color default
        secondary_color="#06b6d4"  # Color default
    )

    if not client:
        print("\n❌ No se pudo crear el cliente. Abortando.")
        return 1

    print()

    # 5. CREAR CENTRO
    print("2️⃣  Creando centro inicial...")
    center = crear_centro_inicial(client.id, nombre_centro)

    if not center:
        print("\n⚠️  No se pudo crear el centro, pero el cliente ya existe.")
        print("   Puedes crear el centro manualmente desde la aplicación.")
        # No abortamos, continuamos con la creación del admin

    print()

    # 6. CREAR ADMINISTRADOR
    print("3️⃣  Creando usuario administrador...")
    admin = create_admin_user(
        client_id=client.id,
        username=username,
        password=password,
        full_name=username,  # Usamos username como nombre completo
        email=None,  # Se generará automáticamente
        client_slug=client.slug
    )

    if not admin:
        print("\n❌ No se pudo crear el usuario administrador.")
        print("ℹ️  El cliente y centro fueron creados exitosamente.")
        print("   Puedes crear el admin manualmente ejecutando este script de nuevo")
        print("   o desde la aplicación.")
        return 1

    print()
    print("=" * 70)
    print("✅ ¡CLIENTE CREADO EXITOSAMENTE!")
    print("=" * 70)
    print()
    print("📊 DETALLES:")
    print(f"  • Empresa: {client.name}")
    print(f"  • Slug: {client.slug}")
    print(f"  • Plan: {client.plan.upper()}")
    print(f"  • ID Cliente: {client.id}")
    print()
    print(f"  • Centro: {nombre_centro}")
    if center:
        print(f"  • ID Centro: {center.id}")
    print()
    print(f"  • Admin: {admin.username}")
    print(f"  • Email: {admin.email}")
    print(f"  • Rol: Super Admin")
    print()
    print("=" * 70)
    print()
    print("💡 PRÓXIMOS PASOS:")
    print("  1. El administrador puede iniciar sesión con las credenciales creadas")
    print("  2. Desde la aplicación puede:")
    print("     - Crear categorías de empleados (Coordinador, Empleado, etc.)")
    print("     - Agregar más centros si el plan es Pro")
    print("     - Crear empleados")
    print()
    print("  O bien, usar los scripts:")
    print(f"     • python add_employee.py           (crear empleados uno a uno)")
    print(f"     • python import_employees_csv.py   (importar múltiples empleados)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
