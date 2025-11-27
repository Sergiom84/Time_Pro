#!/usr/bin/env python3
"""Script para revisar los clientes existentes en la base de datos"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client, User, Center, Category
from main import app

def check_clients():
    """Revisar clientes existentes"""
    with app.app_context():
        print("=" * 70)
        print("CLIENTES EXISTENTES EN TIME PRO")
        print("=" * 70)
        print()

        clients = Client.query.order_by(Client.id).all()

        if not clients:
            print("❌ No hay clientes registrados")
            return

        for client in clients:
            print(f"ID: {client.id}")
            print(f"Nombre: {client.name}")
            print(f"Slug: {client.slug}")
            print(f"Plan: {client.plan.upper()}")
            print(f"Activo: {'Sí' if client.is_active else 'No'}")
            print(f"Logo: {client.logo_url or 'Sin logo'}")
            print(f"Creado: {client.created_at}")

            # Contar usuarios
            users = User.query.filter_by(client_id=client.id).all()
            admins = [u for u in users if u.role in ['admin', 'super_admin']]
            employees = [u for u in users if not u.role]

            print(f"Usuarios: {len(users)} total ({len(admins)} admins, {len(employees)} empleados)")

            # Contar centros y categorías
            centers = Center.query.filter_by(client_id=client.id).count()
            categories = Category.query.filter_by(client_id=client.id).count()

            print(f"Centros: {centers}")
            print(f"Categorías: {categories}")
            print("-" * 70)
            print()

if __name__ == "__main__":
    check_clients()
