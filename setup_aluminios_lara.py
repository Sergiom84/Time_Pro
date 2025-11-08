#!/usr/bin/env python3
"""
Script para configurar Aluminios Lara como primer cliente.

PREREQUISITOS:
1. Ejecutar primero: python3 apply_multitenant_migration.py
2. Tener el logo de Aluminios Lara en una ruta accesible

USO:
    python3 setup_aluminios_lara.py /ruta/al/logo.png
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client, User
from main import app


def setup_aluminios_lara(logo_path=None):
    """
    Configura Aluminios Lara como cliente en Time Pro.

    Args:
        logo_path: Ruta local al logo (opcional)
    """
    with app.app_context():
        try:
            print("=" * 70)
            print("  CONFIGURACIÓN DE ALUMINIOS LARA")
            print("=" * 70)
            print()

            # Paso 1: Verificar si ya existe
            print("1. Verificando si Aluminios Lara ya existe...")
            existing = Client.query.filter_by(slug='aluminios-lara').first()

            if existing:
                print("   ⚠️  Aluminios Lara ya existe en la base de datos")
                print(f"   ID: {existing.id}")
                print(f"   Plan: {existing.plan}")
                print()

                response = input("   ¿Deseas continuar y actualizar? (s/n): ").strip().lower()
                if response != 's':
                    print("   ❌ Operación cancelada")
                    return

                client = existing
                print("   ✅ Actualizando cliente existente...")
            else:
                print("   ✅ Cliente no existe, creando nuevo...")

                # Paso 2: Crear cliente
                client = Client(
                    name="Aluminios Lara",
                    slug="aluminios-lara",
                    plan="pro",  # Puedes cambiar a "lite" si prefieres
                    is_active=True,
                    primary_color="#0ea5e9",  # Azul turquesa
                    secondary_color="#06b6d4"  # Cyan
                )

                db.session.add(client)
                db.session.flush()  # Para obtener el ID sin commit

                print()
                print("2. Cliente 'Aluminios Lara' creado")
                print(f"   ID: {client.id}")
                print(f"   Slug: {client.slug}")
                print(f"   Plan: PRO")

            # Paso 3: Subir logo si se proporciona
            if logo_path and os.path.exists(logo_path):
                print()
                print("3. Subiendo logo a Supabase...")

                try:
                    import requests
                    from config.supabase_config import SUPABASE_URL, SUPABASE_KEY

                    # Leer el archivo
                    with open(logo_path, 'rb') as f:
                        file_content = f.read()

                    # Obtener extensión
                    ext = os.path.splitext(logo_path)[1]

                    # Determinar tipo MIME
                    mime_map = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.svg': 'image/svg+xml',
                    }
                    mime_type = mime_map.get(ext.lower(), 'image/png')

                    # Construir ruta en Supabase
                    storage_path = f"logos/aluminios-lara{ext}"
                    bucket = "Justificantes"

                    # URL de upload
                    upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{storage_path}"

                    headers = {
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Content-Type": mime_type,
                        "x-upsert": "true"
                    }

                    response = requests.post(
                        upload_url,
                        data=file_content,
                        headers=headers,
                        timeout=30
                    )

                    if response.status_code in [200, 201]:
                        # Construir URL pública
                        logo_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
                        client.logo_url = logo_url

                        print(f"   ✅ Logo subido exitosamente")
                        print(f"   URL: {logo_url}")
                    else:
                        print(f"   ⚠️  Error al subir logo - Status: {response.status_code}")
                        print(f"   Puedes subirlo manualmente después")

                except Exception as e:
                    print(f"   ⚠️  Error al subir logo: {e}")
                    print(f"   Puedes subirlo manualmente después")
            elif logo_path:
                print()
                print(f"3. ⚠️  Logo no encontrado en: {logo_path}")
                print("   Puedes subirlo manualmente después")
            else:
                print()
                print("3. Logo no proporcionado (puedes agregarlo después)")

            # Paso 4: Verificar si hay admin
            print()
            print("4. Verificando usuarios administradores...")

            admin = User.query.filter_by(client_id=client.id, is_admin=True).first()

            if admin:
                print(f"   ℹ️  Ya existe un administrador: {admin.username}")
                print(f"   Nombre: {admin.full_name}")
                print(f"   Email: {admin.email}")
            else:
                print("   No hay administradores para este cliente")
                print()

                # Crear admin
                create_admin = input("   ¿Deseas crear un usuario administrador ahora? (s/n): ").strip().lower()

                if create_admin == 's':
                    print()
                    print("   Datos del administrador:")

                    username = input("     Username: ").strip()
                    if not username:
                        print("     ❌ Username requerido. Saltando creación de admin.")
                    else:
                        # Verificar que el username no exista
                        existing_user = User.query.filter_by(username=username).first()
                        if existing_user:
                            print(f"     ❌ El username '{username}' ya existe")
                        else:
                            password = input("     Contraseña: ").strip()
                            full_name = input("     Nombre completo: ").strip()
                            email = input("     Email: ").strip()

                            if password and full_name and email:
                                admin = User(
                                    client_id=client.id,
                                    username=username,
                                    full_name=full_name,
                                    email=email,
                                    is_admin=True,
                                    is_active=True,
                                    weekly_hours=40,
                                    centro="-- Sin categoría --",
                                    categoria="Gestor"
                                )
                                admin.set_password(password)
                                db.session.add(admin)

                                print()
                                print("   ✅ Administrador creado")
                                print(f"   Username: {admin.username}")
                                print(f"   Email: {admin.email}")
                            else:
                                print("     ❌ Datos incompletos. Saltando creación de admin.")

            # Commit final
            db.session.commit()

            print()
            print("=" * 70)
            print("✅ CONFIGURACIÓN COMPLETADA")
            print("=" * 70)
            print()
            print("📋 Resumen:")
            print(f"   Cliente: Aluminios Lara")
            print(f"   ID: {client.id}")
            print(f"   Slug: {client.slug}")
            print(f"   Plan: {client.plan.upper()}")
            if client.logo_url:
                print(f"   Logo: {client.logo_url}")

            admin_count = User.query.filter_by(client_id=client.id, is_admin=True).count()
            employee_count = User.query.filter_by(client_id=client.id, is_admin=False).count()

            print(f"   Administradores: {admin_count}")
            print(f"   Empleados: {employee_count}")
            print()

            print("💡 Próximos pasos:")
            print("   1. Asegúrate de que los usuarios pueden iniciar sesión")
            print("   2. Verifica que el logo se muestre correctamente")
            print("   3. Comienza a usar la aplicación")
            print()

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    logo_path = sys.argv[1] if len(sys.argv) > 1 else None

    if logo_path and not os.path.exists(logo_path):
        print(f"❌ El archivo '{logo_path}' no existe")
        print()
        print("Uso:")
        print("  python3 setup_aluminios_lara.py /ruta/al/logo.png")
        print()
        print("O sin logo:")
        print("  python3 setup_aluminios_lara.py")
        sys.exit(1)

    setup_aluminios_lara(logo_path)
