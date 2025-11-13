#!/usr/bin/env python3
"""
Script directo para:
1. Agregar columna category_id a tabla user
2. Crear categorías en BD
3. Migrar datos de categoria ENUM a category_id FK

Este script ejecuta SQL directo para evitar problemas con Alembic.
"""
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar desde main.py
from main import app
from models.models import db, Client, Category, User
from sqlalchemy import text

def add_category_column():
    """Agrega la columna category_id a la tabla user directamente"""
    with app.app_context():
        print("=" * 60)
        print("PASO 1: Agregando columna category_id a tabla user")
        print("=" * 60)

        try:
            # SQL para agregar columna category_id
            sql = """
            ALTER TABLE "user"
            ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES category(id) ON DELETE SET NULL;
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✅ Columna category_id agregada exitosamente")
            return True
        except Exception as e:
            print(f"⚠️  Columna category_id podría ya existir: {e}")
            return True  # Continuar incluso si ya existe


def setup_categories():
    """Crea las categorías iniciales para cada cliente"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("PASO 2: Creando categorías en Supabase")
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
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar categorías: {e}")
            return False


def migrate_categoria_to_category_id():
    """
    Migra los datos de User.categoria (ENUM) a User.category_id (FK) usando SQL directo.
    Mapea los valores del ENUM a los IDs de la tabla Category.
    """
    with app.app_context():
        print("\n" + "=" * 60)
        print("PASO 3: Migrando datos de categoria → category_id")
        print("=" * 60)

        try:
            # Obtener todos los usuarios con categoria usando SQL directo (columna aún existe en BD)
            result = db.session.execute(text("""
                SELECT id, username, client_id, categoria
                FROM "user"
                WHERE categoria IS NOT NULL AND category_id IS NULL
            """))
            users_data = result.fetchall()

            if not users_data:
                print("\n✓ No hay usuarios para migrar (ya está todo migrado)")
                return True

            print(f"\n🔄 Encontrados {len(users_data)} usuarios para migrar")

            migrated_count = 0
            error_count = 0

            for user_id, username, client_id, categoria_name in users_data:
                try:
                    # Obtener la categoría por nombre desde la tabla Category
                    category = Category.query.filter_by(
                        client_id=client_id,
                        name=categoria_name
                    ).first()

                    if category:
                        # Actualizar category_id usando SQL directo
                        db.session.execute(text("""
                            UPDATE "user" SET category_id = :category_id WHERE id = :user_id
                        """), {"category_id": category.id, "user_id": user_id})
                        migrated_count += 1
                        print(f"   ✓ {username}: {categoria_name} → ID {category.id}")
                    else:
                        print(f"   ⚠️  {username}: No se encontró categoría '{categoria_name}' para client_id={client_id}")
                        error_count += 1

                except Exception as e:
                    print(f"   ❌ Error migrando usuario {user_id}: {e}")
                    error_count += 1

            # Confirmar cambios
            db.session.commit()
            print(f"\n✅ Migración completada: {migrated_count} usuarios actualizados, {error_count} errores")
            return error_count == 0

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al migrar datos: {e}")
            return False


def show_categories():
    """Muestra todas las categorías creadas por cliente"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("RESULTADO: Categorías configuradas")
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


def show_migration_status():
    """Muestra el estado de la migración"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("ESTADO DE MIGRACIÓN")
        print("=" * 60)

        try:
            # Usuarios con categoria (ENUM) pero sin category_id (FK)
            old_style = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
                WHERE categoria IS NOT NULL AND category_id IS NULL
            """)).scalar() or 0

            # Usuarios con category_id (FK)
            new_style = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
                WHERE category_id IS NOT NULL
            """)).scalar() or 0

            # Usuarios sin categoría
            no_category = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
                WHERE categoria IS NULL AND category_id IS NULL
            """)).scalar() or 0

            total = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
            """)).scalar() or 0

            print(f"\n📊 Estadísticas:")
            print(f"   • Usuarios con ENUM categoria: {old_style}")
            print(f"   • Usuarios con FK category_id: {new_style}")
            print(f"   • Usuarios sin categoría: {no_category}")
            print(f"   • TOTAL: {total}")
        except Exception as e:
            print(f"\n❌ Error al obtener estadísticas: {e}")


if __name__ == '__main__':
    print("\n🚀 Starting Direct Category Setup Script...\n")

    # Step 1: Add column
    if not add_category_column():
        print("\n⚠️  Continuando a pesar del error en agregar columna")

    # Step 2: Setup categories
    if not setup_categories():
        print("\n❌ Error al configurar categorías")
        sys.exit(1)

    # Step 3: Migrate data
    if not migrate_categoria_to_category_id():
        print("\n⚠️  Algunos usuarios no se pudieron migrar")

    # Step 4: Show results
    show_categories()
    show_migration_status()

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETADO")
    print("=" * 60)
    print("\nAhora necesitas:")
    print("1. Actualizar los templates HTML para usar categories dinámicas")
    print("2. Actualizar rutas admin para permitir edición de categorías por cliente")
    print()
