#!/usr/bin/env python3
"""
Script para agregar empleados de prueba al cliente Patacones de mi tierra
Recuerda: Plan LITE = máximo 5 empleados
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client, User, Center, Category
from main import app

def add_test_employees():
    """Agregar empleados de prueba al cliente Patacones"""
    with app.app_context():
        # Buscar el cliente
        client = Client.query.filter_by(slug='patacones-de-mi-tierra').first()

        if not client:
            print("❌ Error: Cliente 'Patacones de mi tierra' no encontrado.")
            print("   Por favor, ejecuta primero: python create_patacones_client.py")
            return 1

        print("=" * 70)
        print(f"AÑADIENDO EMPLEADOS DE PRUEBA A: {client.name}")
        print("=" * 70)
        print()

        # Verificar cuántos usuarios ya tiene el cliente
        existing_users = User.query.filter_by(client_id=client.id).count()
        print(f"👥 Usuarios existentes: {existing_users}")

        if client.plan == 'lite' and existing_users >= 5:
            print("⚠️  ADVERTENCIA: Plan LITE permite máximo 5 empleados.")
            print(f"   Ya tienes {existing_users} usuarios. No se pueden añadir más.")
            return 1

        # Obtener el centro principal
        center = Center.query.filter_by(client_id=client.id).first()
        if not center:
            print("❌ Error: No se encontró ningún centro para este cliente.")
            return 1

        # Obtener categorías
        category_camarero = Category.query.filter_by(
            client_id=client.id,
            name="Camarero"
        ).first()

        category_cocinero = Category.query.filter_by(
            client_id=client.id,
            name="Cocinero"
        ).first()

        # Definir empleados de prueba
        # Nota: Solo agregamos hasta completar 5 empleados (incluyendo el admin)
        max_employees = 5 if client.plan == 'lite' else 100
        available_slots = max_employees - existing_users

        employees_to_create = [
            {
                "username": "maria_gomez",
                "password": "Maria2025!",
                "full_name": "María Gómez",
                "email": "maria.gomez@pataconesdetierra.com",
                "category_id": category_camarero.id if category_camarero else None,
                "weekly_hours": 40
            },
            {
                "username": "carlos_rodriguez",
                "password": "Carlos2025!",
                "full_name": "Carlos Rodríguez",
                "email": "carlos.rodriguez@pataconesdetierra.com",
                "category_id": category_cocinero.id if category_cocinero else None,
                "weekly_hours": 40
            },
            {
                "username": "ana_martinez",
                "password": "Ana2025!",
                "full_name": "Ana Martínez",
                "email": "ana.martinez@pataconesdetierra.com",
                "category_id": category_camarero.id if category_camarero else None,
                "weekly_hours": 30
            },
            {
                "username": "juan_lopez",
                "password": "Juan2025!",
                "full_name": "Juan López",
                "email": "juan.lopez@pataconesdetierra.com",
                "category_id": category_cocinero.id if category_cocinero else None,
                "weekly_hours": 40
            }
        ]

        # Limitar a los slots disponibles
        employees_to_create = employees_to_create[:available_slots]

        if not employees_to_create:
            print("⚠️  No hay slots disponibles para más empleados.")
            return 0

        print(f"📝 Se crearán {len(employees_to_create)} empleados de prueba")
        print()

        created_count = 0
        for emp_data in employees_to_create:
            # Verificar si el usuario ya existe
            existing = User.query.filter_by(
                client_id=client.id,
                username=emp_data["username"]
            ).first()

            if existing:
                print(f"⚠️  El usuario '{emp_data['username']}' ya existe. Saltando...")
                continue

            # Crear el empleado
            employee = User(
                client_id=client.id,
                username=emp_data["username"],
                full_name=emp_data["full_name"],
                email=emp_data["email"],
                role=None,  # Usuario normal (no admin)
                is_active=True,
                weekly_hours=emp_data["weekly_hours"],
                center_id=center.id,
                category_id=emp_data["category_id"],
                theme_preference='dark-turquoise'
            )

            employee.set_password(emp_data["password"])

            db.session.add(employee)

            try:
                db.session.commit()
                created_count += 1
                print(f"✅ Empleado creado: {emp_data['full_name']} ({emp_data['username']})")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error al crear {emp_data['username']}: {e}")

        print()
        print("=" * 70)
        print(f"✅ PROCESO COMPLETADO")
        print("=" * 70)
        print()
        print(f"Empleados creados: {created_count}")
        print(f"Total de usuarios en el cliente: {existing_users + created_count}")
        print()

        if client.plan == 'lite':
            print(f"⚠️  Plan LITE: {existing_users + created_count}/5 empleados utilizados")
            print()

        print("CREDENCIALES DE LOS EMPLEADOS DE PRUEBA:")
        print("-" * 70)
        for emp_data in employees_to_create[:created_count]:
            print(f"Usuario: {emp_data['username']}")
            print(f"Nombre: {emp_data['full_name']}")
            print(f"Email: {emp_data['email']}")
            print(f"Password: {emp_data['password']}")
            print("-" * 70)

        print()
        print("💡 Los empleados pueden ahora iniciar sesión en la aplicación.")
        print()

        return 0

if __name__ == "__main__":
    sys.exit(add_test_employees())
