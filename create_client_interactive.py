#!/usr/bin/env python3
"""
Script interactivo para crear un nuevo cliente en Time Pro
Sin valores hardcodeados - todo configurable por el usuario
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.setup_client import create_client, create_admin_user


def main():
    print("=" * 70)
    print("TIME PRO - CREAR NUEVO CLIENTE")
    print("=" * 70)
    print()
    print("Este script te ayudará a crear un nuevo cliente paso a paso.")
    print()

    # 1. Datos del cliente
    print("PASO 1: DATOS DEL CLIENTE")
    print("-" * 70)

    client_name = input("Nombre del cliente (ej: Patacones de mi tierra): ").strip()
    if not client_name:
        print("❌ El nombre del cliente es obligatorio")
        return 1

    # Plan
    while True:
        plan = input("Plan (lite/pro) [lite]: ").strip().lower() or "lite"
        if plan in ['lite', 'pro']:
            break
        print("❌ Plan inválido. Debe ser 'lite' o 'pro'")

    # Logo (opcional)
    logo_path = input("Ruta al logo (Enter para omitir): ").strip()
    if logo_path and not os.path.exists(logo_path):
        print(f"⚠️  El archivo '{logo_path}' no existe")
        use_anyway = input("¿Continuar sin logo? (s/n): ").strip().lower()
        if use_anyway != 's':
            return 1
        logo_path = None

    # Colores (opcional)
    print()
    print("Colores personalizados (Enter para usar defaults):")
    primary_color = input("  Color principal [#0ea5e9]: ").strip() or "#0ea5e9"
    secondary_color = input("  Color secundario [#06b6d4]: ").strip() or "#06b6d4"

    print()
    print("=" * 70)
    print("RESUMEN DEL CLIENTE")
    print("=" * 70)
    print(f"Nombre: {client_name}")
    print(f"Plan: {plan.upper()}")
    print(f"Logo: {logo_path or 'Sin logo'}")
    print(f"Color principal: {primary_color}")
    print(f"Color secundario: {secondary_color}")
    print()

    confirm = input("¿Crear este cliente? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Operación cancelada")
        return 1

    print()
    print("📝 Creando cliente...")
    client = create_client(
        name=client_name,
        plan=plan,
        logo_path=logo_path,
        primary_color=primary_color,
        secondary_color=secondary_color
    )

    if not client:
        print("\n❌ Error al crear el cliente. Abortando.")
        return 1

    # 2. Datos del administrador
    print()
    print("=" * 70)
    print("PASO 2: DATOS DEL ADMINISTRADOR")
    print("=" * 70)
    print()

    admin_username = input("Username del administrador: ").strip()
    if not admin_username:
        print("❌ El username es obligatorio")
        return 1

    admin_password = input("Contraseña: ").strip()
    if not admin_password:
        print("❌ La contraseña es obligatoria")
        return 1

    # Confirmar contraseña
    admin_password_confirm = input("Confirmar contraseña: ").strip()
    if admin_password != admin_password_confirm:
        print("❌ Las contraseñas no coinciden")
        return 1

    admin_full_name = input("Nombre completo: ").strip()
    if not admin_full_name:
        print("❌ El nombre completo es obligatorio")
        return 1

    admin_email = input("Email: ").strip()
    if not admin_email:
        print("⚠️  Email no proporcionado. Se generará uno automático.")

    print()
    print("=" * 70)
    print("RESUMEN DEL ADMINISTRADOR")
    print("=" * 70)
    print(f"Username: {admin_username}")
    print(f"Nombre completo: {admin_full_name}")
    print(f"Email: {admin_email or '(se generará automáticamente)'}")
    print()

    confirm = input("¿Crear este administrador? (s/n): ").strip().lower()
    if confirm != 's':
        print("❌ Operación cancelada")
        return 1

    print()
    print("📝 Creando administrador...")
    admin = create_admin_user(
        client_id=client.id,
        username=admin_username,
        password=admin_password,
        full_name=admin_full_name,
        email=admin_email,
        client_slug=client.slug
    )

    if not admin:
        print("\n❌ Error al crear el administrador")
        return 1

    # Resumen final
    print()
    print("=" * 70)
    print("✅ ¡CLIENTE CREADO EXITOSAMENTE!")
    print("=" * 70)
    print()
    print(f"CLIENTE: {client.name}")
    print(f"  Slug: {client.slug}")
    print(f"  Plan: {client.plan.upper()}")
    print(f"  ID: {client.id}")
    print()
    print(f"ADMINISTRADOR: {admin.full_name}")
    print(f"  Username: {admin.username}")
    print(f"  Email: {admin.email}")
    print()
    print("=" * 70)
    print("CREDENCIALES DE ACCESO")
    print("=" * 70)
    print(f"URL: http://localhost:5000")
    print(f"Username: {admin.username}")
    print(f"Password: {admin_password}")
    print()
    print("💡 Guarda estas credenciales en un lugar seguro.")
    print()
    print("PRÓXIMOS PASOS:")
    print("1. Ejecuta: python main.py")
    print("2. Abre tu navegador en: http://localhost:5000")
    print("3. Inicia sesión con las credenciales de arriba")
    print("4. (Opcional) Ejecuta: python add_employees_interactive.py")
    print("   para añadir empleados de prueba")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
