#!/usr/bin/env python3
"""
Script para configurar un nuevo cliente en Time Pro.
Uso: python scripts/setup_client.py
"""
import sys
import os
import re
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import db
from models.models import Client, User
from main import app
import requests
from config.supabase_config import SUPABASE_URL, SUPABASE_KEY


def slugify(text):
    """
    Convierte texto a slug (ej: "Aluminios Lara" -> "aluminios-lara")
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def upload_logo_to_supabase(logo_path, client_slug):
    """
    Sube el logo del cliente a Supabase Storage.

    Args:
        logo_path: Ruta local del logo
        client_slug: Slug del cliente

    Returns:
        URL del logo subido o None si hay error
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(logo_path):
            print(f"❌ Error: El archivo {logo_path} no existe")
            return None

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
        storage_path = f"logos/{client_slug}{ext}"
        bucket = "Justificantes"  # Reutilizamos el bucket existente

        # URL de upload
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{storage_path}"

        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": mime_type,
            "x-upsert": "true"
        }

        print(f"📤 Subiendo logo a Supabase...")
        response = requests.post(
            upload_url,
            data=file_content,
            headers=headers,
            timeout=30
        )

        if response.status_code not in [200, 201]:
            print(f"❌ Error al subir logo - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

        print(f"✅ Logo subido exitosamente")

        # Construir URL pública
        logo_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"

        return logo_url

    except Exception as e:
        print(f"❌ Error al subir logo: {e}")
        return None


def create_client(name, plan, logo_path=None, primary_color="#0ea5e9", secondary_color="#06b6d4"):
    """
    Crea un nuevo cliente en la base de datos.

    Args:
        name: Nombre del cliente (ej: "Aluminios Lara")
        plan: Plan del cliente ("lite" o "pro")
        logo_path: Ruta local al logo (opcional)
        primary_color: Color principal en formato hex
        secondary_color: Color secundario en formato hex

    Returns:
        Objeto Client creado o None si hay error
    """
    with app.app_context():
        try:
            # Generar slug
            slug = slugify(name)

            # Verificar que no exista
            existing = Client.query.filter_by(slug=slug).first()
            if existing:
                print(f"ℹ️  Ya existe un cliente con slug '{slug}'. Continuando con creación/actualización de admin...")
                return existing

            # Subir logo si se proporcionó
            logo_url = None
            if logo_path:
                logo_url = upload_logo_to_supabase(logo_path, slug)
                if not logo_url:
                    print("⚠️  No se pudo subir el logo, continuando sin logo...")

            # Crear cliente
            client = Client(
                name=name,
                slug=slug,
                plan=plan,
                logo_url=logo_url,
                is_active=True,
                primary_color=primary_color,
                secondary_color=secondary_color
            )

            db.session.add(client)
            db.session.commit()

            print(f"✅ Cliente '{name}' creado exitosamente")
            print(f"   ID: {client.id}")
            print(f"   Slug: {client.slug}")
            print(f"   Plan: {client.plan}")
            if logo_url:
                print(f"   Logo: {logo_url}")

            return client

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear cliente: {e}")
            import traceback
            traceback.print_exc()
            return None


def _generate_placeholder_email(slug: str, username: str) -> str:
    safe_user = re.sub(r"[^a-z0-9]+", "-", username.lower()) or "admin"
    safe_slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()) or "cliente"
    return f"{safe_user}+{safe_slug}@placeholder.local"


def create_admin_user(client_id, username, password, full_name, email, client_slug: str | None = None):
    """
    Crea el usuario administrador inicial para un cliente.

    Args:
        client_id: ID del cliente
        username: Nombre de usuario
        password: Contraseña
        full_name: Nombre completo
        email: Email

    Returns:
        Objeto User creado o None si hay error
    """
    with app.app_context():
        try:
            # Verificar que el username no exista EN ESTE CLIENTE
            existing = User.query.filter_by(client_id=client_id, username=username).first()
            if existing:
                # Actualizar datos del usuario existente (upsert)
                print(f"ℹ️  Usuario '{username}' ya existe en este cliente. Actualizando datos...")
                if full_name:
                    existing.full_name = full_name
                if email:
                    # Validar unicidad por cliente para email si cambia
                    if existing.email != email:
                        dup = User.query.filter_by(client_id=client_id, email=email).first()
                        if dup:
                            print(f"❌ Error: Ya existe un usuario con email '{email}' en este cliente")
                            return None
                        existing.email = email
                if password:
                    existing.set_password(password)
                db.session.commit()
                print(f"✅ Usuario administrador actualizado")
                print(f"   ID: {existing.id}")
                print(f"   Username: {existing.username}")
                print(f"   Email: {existing.email}")
                return existing

            # Si no se proporciona email, generar uno placeholder único
            if not email:
                email = _generate_placeholder_email(client_slug or "cliente", username)
                # Asegurar unicidad si existiera
                counter = 1
                base_email = email
                while User.query.filter_by(client_id=client_id, email=email).first():
                    email = base_email.replace("@", f"+{counter}@")
                    counter += 1
                print(f"⚠️  Email no proporcionado. Usando placeholder: {email}")
            else:
                # Verificar que el email no exista
                existing_email = User.query.filter_by(client_id=client_id, email=email).first()
                if existing_email:
                    print(f"❌ Error: Ya existe un usuario con email '{email}'")
                    return None

            # Crear usuario administrador
            user = User(
                client_id=client_id,
                username=username,
                full_name=full_name,
                email=email,
                role='super_admin',  # Super admin del cliente
                is_active=True,
                weekly_hours=40,
                center_id=None,  # Super admin sin centro específico
                category_id=None
            )

            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            print(f"✅ Usuario administrador creado exitosamente")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")

            return user

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear usuario administrador: {e}")
            import traceback
            traceback.print_exc()
            return None


def interactive_setup():
    """
    Modo interactivo para configurar un nuevo cliente.
    """
    print("=" * 60)
    print("    TIME PRO - CONFIGURACIÓN DE NUEVO CLIENTE")
    print("=" * 60)
    print()

    # Solicitar datos del cliente
    name = input("Nombre del cliente (ej: Aluminios Lara): ").strip()
    if not name:
        print("❌ El nombre es requerido")
        return

    # Validar plan
    while True:
        plan = input("Plan (lite/pro) [pro]: ").strip().lower() or "pro"
        if plan in ['lite', 'pro']:
            break
        print("❌ Plan inválido. Debe ser 'lite' o 'pro'")

    # Solicitar logo (opcional)
    logo_path = input("Ruta al logo (Enter para omitir): ").strip()
    if logo_path and not os.path.exists(logo_path):
        print(f"⚠️  El archivo '{logo_path}' no existe, continuando sin logo...")
        logo_path = None

    # Colores personalizados (opcional)
    print("\nColores personalizados (Enter para usar defaults):")
    primary_color = input("  Color principal [#0ea5e9]: ").strip() or "#0ea5e9"
    secondary_color = input("  Color secundario [#06b6d4]: ").strip() or "#06b6d4"

    print("\n" + "-" * 60)
    print("CREANDO CLIENTE...")
    print("-" * 60)

    # Crear cliente
    client = create_client(
        name=name,
        plan=plan,
        logo_path=logo_path,
        primary_color=primary_color,
        secondary_color=secondary_color
    )

    if not client:
        print("\n❌ No se pudo crear el cliente. Abortando.")
        return

    print("\n" + "-" * 60)
    print("CREANDO USUARIO ADMINISTRADOR...")
    print("-" * 60)

    # Solicitar datos del admin
    username = input("Username del administrador: ").strip()
    if not username:
        print("❌ El username es requerido")
        # Eliminar cliente creado
        with app.app_context():
            db.session.delete(client)
            db.session.commit()
        return

    password = input("Contraseña: ").strip()
    if not password:
        print("❌ La contraseña es requerida")
        # Eliminar cliente creado
        with app.app_context():
            db.session.delete(client)
            db.session.commit()
        return

    full_name = input("Nombre completo: ").strip()
    if not full_name:
        print("❌ El nombre completo es requerido")
        # Eliminar cliente creado
        with app.app_context():
            db.session.delete(client)
            db.session.commit()
        return

    email = input("Email (Enter para omitir): ").strip()

    # Crear admin
    admin = create_admin_user(
        client_id=client.id,
        username=username,
        password=password,
        full_name=full_name,
        email=email,
        client_slug=client.slug
    )

    if not admin:
        print("\n❌ No se pudo crear el usuario administrador.")
        print("ℹ️  El cliente permanece creado. Puedes volver a ejecutar este script solo para crear el admin o usar src/create_admin.py.")
        return

    print("\n" + "=" * 60)
    print("✅ ¡CONFIGURACIÓN COMPLETADA!")
    print("=" * 60)
    print(f"\nCliente: {client.name}")
    print(f"Slug: {client.slug}")
    print(f"Plan: {client.plan.upper()}")
    print(f"\nAdministrador: {admin.full_name}")
    print(f"Username: {admin.username}")
    print(f"Email: {admin.email}")
    print("\n💡 El administrador puede ahora iniciar sesión en la aplicación.")
    print()


if __name__ == "__main__":
    interactive_setup()
