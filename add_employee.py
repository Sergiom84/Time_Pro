#!/usr/bin/env python3
"""
Script interactivo para añadir empleados a un cliente
Sin valores hardcodeados - todo configurable por el usuario
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client, User, Center, Category
from main import app


def select_client():
    """Permite al usuario seleccionar un cliente"""
    with app.app_context():
        clients = Client.query.order_by(Client.name).all()

        if not clients:
            print("❌ No hay clientes en la base de datos")
            print("   Ejecuta primero: python create_client_interactive.py")
            return None

        print()
        print("CLIENTES DISPONIBLES:")
        print("-" * 70)
        for idx, client in enumerate(clients, 1):
            user_count = User.query.filter_by(client_id=client.id).count()
            print(f"{idx}. {client.name} ({client.plan.upper()}) - {user_count} usuarios")
        print()

        while True:
            try:
                selection = input(f"Selecciona un cliente (1-{len(clients)}): ").strip()
                idx = int(selection) - 1
                if 0 <= idx < len(clients):
                    return clients[idx]
                print(f"❌ Número inválido. Debe estar entre 1 y {len(clients)}")
            except ValueError:
                print("❌ Debe ser un número")


def select_category(client_id):
    """Permite al usuario seleccionar una categoría"""
    with app.app_context():
        categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()

        if not categories:
            print("⚠️  No hay categorías configuradas para este cliente")
            return None

        print()
        print("CATEGORÍAS DISPONIBLES:")
        print("-" * 70)
        for idx, cat in enumerate(categories, 1):
            print(f"{idx}. {cat.name}")
        print()

        while True:
            try:
                selection = input(f"Selecciona una categoría (1-{len(categories)}, Enter para omitir): ").strip()
                if not selection:
                    return None
                idx = int(selection) - 1
                if 0 <= idx < len(categories):
                    return categories[idx]
                print(f"❌ Número inválido. Debe estar entre 1 y {len(categories)}")
            except ValueError:
                print("❌ Debe ser un número")


def add_employee_interactive(client):
    """Añade un empleado de forma interactiva"""
    with app.app_context():
        print()
        print("=" * 70)
        print("AÑADIR NUEVO EMPLEADO")
        print("=" * 70)
        print()

        # Verificar límites del plan
        existing_users = User.query.filter_by(client_id=client.id).count()

        if client.plan == 'lite' and existing_users >= 10:
            print("❌ ERROR: Plan LITE permite máximo 10 empleados")
            print(f"   Este cliente ya tiene {existing_users} usuarios")
            print("   Para añadir más empleados, actualiza el plan a PRO")
            return False

        print(f"Cliente: {client.name}")
        print(f"Plan: {client.plan.upper()}")
        print(f"Empleados actuales: {existing_users}")
        if client.plan == 'lite':
            print(f"Límite: 10 empleados")
            print(f"Disponibles: {10 - existing_users}")
        print()

        # Datos del empleado
        username = input("Username del empleado: ").strip()
        if not username:
            print("❌ El username es obligatorio")
            return False

        # Verificar que no exista
        existing = User.query.filter_by(client_id=client.id, username=username).first()
        if existing:
            print(f"❌ El username '{username}' ya existe en este cliente")
            return False

        password = input("Contraseña: ").strip()
        if not password:
            print("❌ La contraseña es obligatoria")
            return False

        password_confirm = input("Confirmar contraseña: ").strip()
        if password != password_confirm:
            print("❌ Las contraseñas no coinciden")
            return False

        full_name = input("Nombre completo: ").strip()
        if not full_name:
            print("❌ El nombre completo es obligatorio")
            return False

        email = input("Email: ").strip()
        if not email:
            print("❌ El email es obligatorio")
            return False

        # Verificar que el email no exista
        existing_email = User.query.filter_by(client_id=client.id, email=email).first()
        if existing_email:
            print(f"❌ El email '{email}' ya existe en este cliente")
            return False

        while True:
            try:
                weekly_hours = input("Horas semanales [40]: ").strip() or "40"
                weekly_hours = int(weekly_hours)
                if weekly_hours > 0:
                    break
                print("❌ Las horas semanales deben ser mayor a 0")
            except ValueError:
                print("❌ Debe ser un número")

        # Seleccionar centro
        center = Center.query.filter_by(client_id=client.id).first()
        if not center:
            print("❌ ERROR: No hay centros configurados para este cliente")
            return False

        # Seleccionar categoría
        category = select_category(client.id)

        # Resumen
        print()
        print("=" * 70)
        print("RESUMEN DEL EMPLEADO")
        print("=" * 70)
        print(f"Username: {username}")
        print(f"Nombre completo: {full_name}")
        print(f"Email: {email}")
        print(f"Horas semanales: {weekly_hours}")
        print(f"Centro: {center.name}")
        print(f"Categoría: {category.name if category else 'Sin categoría'}")
        print()

        confirm = input("¿Crear este empleado? (s/n): ").strip().lower()
        if confirm != 's':
            print("❌ Operación cancelada")
            return False

        # Crear empleado
        employee = User(
            client_id=client.id,
            username=username,
            full_name=full_name,
            email=email,
            role=None,  # Usuario normal (no admin)
            is_active=True,
            weekly_hours=weekly_hours,
            center_id=center.id,
            category_id=category.id if category else None,
            theme_preference='dark-turquoise'
        )

        employee.set_password(password)

        try:
            db.session.add(employee)
            db.session.commit()

            print()
            print("✅ Empleado creado exitosamente")
            print(f"   ID: {employee.id}")
            print(f"   Username: {employee.username}")
            print(f"   Email: {employee.email}")
            print()

            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear empleado: {e}")
            return False


def main():
    print("=" * 70)
    print("TIME PRO - AÑADIR EMPLEADOS")
    print("=" * 70)

    # Seleccionar cliente
    client = select_client()
    if not client:
        return 1

    print()
    print(f"Cliente seleccionado: {client.name}")
    print()

    # Añadir empleados
    employees_added = 0

    while True:
        if add_employee_interactive(client):
            employees_added += 1

            # Verificar si se alcanzó el límite
            with app.app_context():
                total_users = User.query.filter_by(client_id=client.id).count()
                if client.plan == 'lite' and total_users >= 10:
                    print()
                    print("⚠️  Has alcanzado el límite de 10 empleados del plan LITE")
                    break

        print()
        another = input("¿Añadir otro empleado? (s/n): ").strip().lower()
        if another != 's':
            break

    print()
    print("=" * 70)
    print(f"✅ PROCESO COMPLETADO")
    print("=" * 70)
    print(f"Empleados añadidos: {employees_added}")
    print()
    print("Para iniciar la aplicación:")
    print("  python main.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
