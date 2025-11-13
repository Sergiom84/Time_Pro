#!/usr/bin/env python3
"""
Script directo para:
1. Agregar columna center_id a tabla user
2. Migrar datos de centro ENUM a center_id FK

Este script ejecuta SQL directo para evitar problemas con Alembic.
"""
import os
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar desde main.py
from main import app
from models.models import db, Client, Center, User
from sqlalchemy import text

def add_center_id_column():
    """Agrega la columna center_id a la tabla user directamente"""
    with app.app_context():
        print("=" * 60)
        print("PASO 1: Agregando columna center_id a tabla user")
        print("=" * 60)

        try:
            # SQL para agregar columna center_id
            sql = """
            ALTER TABLE "user"
            ADD COLUMN IF NOT EXISTS center_id INTEGER REFERENCES center(id) ON DELETE SET NULL;
            """
            db.session.execute(text(sql))
            db.session.commit()
            print("✅ Columna center_id agregada exitosamente")
            return True
        except Exception as e:
            print(f"⚠️  Columna center_id podría ya existir: {e}")
            return True  # Continuar incluso si ya existe


def migrate_centro_to_center_id():
    """
    Migra los datos de User.centro (ENUM) a User.center_id (FK).
    Mapea los valores del ENUM a los IDs de la tabla Center.
    """
    with app.app_context():
        print("\n" + "=" * 60)
        print("PASO 2: Migrando datos de centro → center_id")
        print("=" * 60)

        try:
            # Obtener todos los usuarios con centro usando SQL directo (columna aún existe en BD)
            result = db.session.execute(text("""
                SELECT id, username, client_id, centro
                FROM "user"
                WHERE centro IS NOT NULL AND center_id IS NULL
            """))
            users_data = result.fetchall()

            if not users_data:
                print("\n✓ No hay usuarios para migrar (ya está todo migrado)")
                return True

            print(f"\n🔄 Encontrados {len(users_data)} usuarios para migrar")

            migrated_count = 0
            error_count = 0

            for user_id, username, client_id, centro_name in users_data:
                try:
                    # Obtener el centro por nombre desde la tabla Center
                    center = Center.query.filter_by(
                        client_id=client_id,
                        name=centro_name
                    ).first()

                    if center:
                        # Actualizar center_id usando SQL directo
                        db.session.execute(text("""
                            UPDATE "user" SET center_id = :center_id WHERE id = :user_id
                        """), {"center_id": center.id, "user_id": user_id})
                        migrated_count += 1
                        print(f"   ✓ {username}: {centro_name} → ID {center.id}")
                    else:
                        print(f"   ⚠️  {username}: No se encontró centro '{centro_name}' para client_id={client_id}")
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


def show_centers_by_client():
    """Muestra los centros agrupados por cliente"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("RESULTADO: Centros configurados")
        print("=" * 60)

        clients = Client.query.all()

        for client in clients:
            centers = Center.query.filter_by(client_id=client.id).all()
            print(f"\n📊 {client.name} (ID: {client.id})")
            if centers:
                for ctr in centers:
                    users_count = User.query.filter_by(center_id=ctr.id).count()
                    print(f"   • {ctr.name} (ID: {ctr.id}) - {users_count} usuarios")
            else:
                print("   ⚠️  Sin centros")


def show_migration_status():
    """Muestra el estado de la migración"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("ESTADO DE MIGRACIÓN")
        print("=" * 60)

        try:
            # Usuarios con centro (ENUM) pero sin center_id (FK)
            old_style = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
                WHERE centro IS NOT NULL AND center_id IS NULL
            """)).scalar() or 0

            # Usuarios con center_id (FK)
            new_style = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
                WHERE center_id IS NOT NULL
            """)).scalar() or 0

            # Usuarios sin centro
            no_center = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
                WHERE centro IS NULL AND center_id IS NULL
            """)).scalar() or 0

            total = db.session.execute(text("""
                SELECT COUNT(*) FROM "user"
            """)).scalar() or 0

            print(f"\n📊 Estadísticas:")
            print(f"   • Usuarios con ENUM centro: {old_style}")
            print(f"   • Usuarios con FK center_id: {new_style}")
            print(f"   • Usuarios sin centro: {no_center}")
            print(f"   • TOTAL: {total}")
        except Exception as e:
            print(f"\n❌ Error al obtener estadísticas: {e}")


if __name__ == '__main__':
    print("\n🚀 Starting Direct Center Setup Script...\n")

    # Step 1: Add column
    if not add_center_id_column():
        print("\n⚠️  Continuando a pesar del error en agregar columna")

    # Step 2: Migrate data
    if not migrate_centro_to_center_id():
        print("\n⚠️  Algunos usuarios no se pudieron migrar")

    # Step 3: Show results
    show_centers_by_client()
    show_migration_status()

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETADO")
    print("=" * 60)
    print("\nAhora necesitas:")
    print("1. Actualizar rutas admin para CRUD de centros")
    print("2. Actualizar templates para selectores dinámicos")
    print()
