#!/usr/bin/env python3
"""
Script para poblar la tabla de categorías en Supabase.
Este script:
1. Crea categorías por defecto (Coordinador, Empleado, Gestor) para todos los clientes
2. Para client_id=4, solo crea Gestor y Empleado (como solicitado)
3. Migra datos de User.categoria (ENUM) a User.category_id (FK)
"""
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar desde main.py
from main import app
from models.models import db, Client, Category, User

def setup_categories():
    """Crea las categorías iniciales para cada cliente"""
    with app.app_context():
        print("=" * 60)
        print("INICIANDO SETUP DE CATEGORÍAS")
        print("=" * 60)

        # Obtener todos los clientes
        clients = Client.query.all()

        if not clients:
            print("❌ No hay clientes en la BD")
            return False

        default_categories = ["Coordinador", "Empleado", "Gestor"]
        client_4_categories = ["Gestor", "Empleado"]  # Solo estas dos para client_id=4

        for client in clients:
            print(f"\n📊 Cliente: {client.name} (ID: {client.id})")

            # Determinar qué categorías asignar a este cliente
            if client.id == 4:
                categories_for_client = client_4_categories
                print(f"   ✅ Cliente especial - usando solo: {categories_for_client}")
            else:
                categories_for_client = default_categories
                print(f"   ✅ Usando categorías por defecto: {categories_for_client}")

            # Crear categorías para este cliente
            for category_name in categories_for_client:
                # Verificar si la categoría ya existe
                existing = Category.query.filter_by(
                    client_id=client.id,
                    name=category_name
                ).first()

                if existing:
                    print(f"      ✓ Categoría '{category_name}' ya existe")
                else:
                    # Crear nueva categoría
                    category = Category(
                        client_id=client.id,
                        name=category_name,
                        description=f"Categoría {category_name} para {client.name}"
                    )
                    db.session.add(category)
                    print(f"      ➕ Categoría '{category_name}' creada")

        # Confirmar cambios
        try:
            db.session.commit()
            print("\n✅ Categorías guardadas en la BD")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar categorías: {e}")
            return False

        return True


def migrate_categoria_to_category_id():
    """
    Migra los datos de User.categoria (ENUM) a User.category_id (FK).
    Mapea los valores del ENUM a los IDs de la tabla Category.
    """
    with app.app_context():
        print("\n" + "=" * 60)
        print("MIGRANDO DATOS DE categoria → category_id")
        print("=" * 60)

        # Obtener todos los usuarios que tienen categoria (ENUM) pero no category_id (FK)
        users_to_migrate = User.query.filter(
            User.categoria_old.isnot(None),
            User.category_id.is_(None)
        ).all()

        if not users_to_migrate:
            print("\n✓ No hay usuarios para migrar (ya está todo migrado)")
            return True

        print(f"\n🔄 Encontrados {len(users_to_migrate)} usuarios para migrar")

        migrated_count = 0
        error_count = 0

        for user in users_to_migrate:
            try:
                # Obtener la categoría por nombre desde la tabla Category
                category = Category.query.filter_by(
                    client_id=user.client_id,
                    name=user.categoria_old
                ).first()

                if category:
                    user.category_id = category.id
                    migrated_count += 1
                    print(f"   ✓ {user.username}: {user.categoria_old} → ID {category.id}")
                else:
                    print(f"   ⚠️  {user.username}: No se encontró categoría '{user.categoria_old}' para client_id={user.client_id}")
                    error_count += 1

            except Exception as e:
                print(f"   ❌ Error migrando {user.username}: {e}")
                error_count += 1

        # Confirmar cambios
        try:
            db.session.commit()
            print(f"\n✅ Migración completada: {migrated_count} usuarios actualizados, {error_count} errores")
            return error_count == 0
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar migración: {e}")
            return False


def show_categories():
    """Muestra todas las categorías creadas por cliente"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("CATEGORÍAS CONFIGURADAS")
        print("=" * 60)

        clients = Client.query.all()

        for client in clients:
            categories = Category.query.filter_by(client_id=client.id).all()
            print(f"\n📊 {client.name} (ID: {client.id})")
            if categories:
                for cat in categories:
                    users_count = User.query.filter_by(category_id=cat.id).count()
                    print(f"   • {cat.name} (ID: {cat.id}) - {users_count} usuarios")
            else:
                print("   ⚠️  Sin categorías")


if __name__ == '__main__':
    print("\n🚀 Starting Category Setup Script...\n")

    # Step 1: Setup categories
    if not setup_categories():
        print("\n❌ Error al configurar categorías")
        sys.exit(1)

    # Step 2: Migrate data
    if not migrate_categoria_to_category_id():
        print("\n❌ Error al migrar datos")
        sys.exit(1)

    # Step 3: Show results
    show_categories()

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print("\nPróximos pasos:")
    print("1. Ejecutar: python -m flask db migrate")
    print("2. Ejecutar: python -m flask db upgrade")
    print("3. Actualizar templates HTML para usar categories dinámicas")
    print()
