#!/usr/bin/env python3
"""
Script para actualizar un cliente existente
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client
from main import app


def update_client(client_id, new_name, new_slug=None, new_logo_url=None):
    """Actualiza los datos de un cliente existente"""
    with app.app_context():
        client = Client.query.get(client_id)

        if not client:
            print(f"❌ Cliente con ID {client_id} no encontrado")
            return False

        print(f"Cliente actual: {client.name} ({client.slug})")
        print()

        # Actualizar datos
        client.name = new_name

        if new_slug:
            # Verificar que el nuevo slug no exista
            existing = Client.query.filter_by(slug=new_slug).first()
            if existing and existing.id != client_id:
                print(f"❌ Ya existe un cliente con slug '{new_slug}'")
                return False
            client.slug = new_slug

        if new_logo_url:
            client.logo_url = new_logo_url

        try:
            db.session.commit()
            print(f"✅ Cliente actualizado exitosamente")
            print(f"   Nuevo nombre: {client.name}")
            print(f"   Nuevo slug: {client.slug}")
            if new_logo_url:
                print(f"   Nuevo logo: {client.logo_url}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al actualizar cliente: {e}")
            return False


if __name__ == "__main__":
    print("=" * 70)
    print("ACTUALIZAR CLIENTE: PruebaCo → Patacones de mi tierra")
    print("=" * 70)
    print()

    success = update_client(
        client_id=2,  # ID de PruebaCo
        new_name="Patacones de mi tierra",
        new_slug="patacones-de-mi-tierra",
        new_logo_url=None  # Mantener el logo actual por ahora
    )

    if success:
        print()
        print("=" * 70)
        print("SIGUIENTE PASO: CREAR ADMINISTRADOR")
        print("=" * 70)
        print()
        print("Ejecuta:")
        print("  python scripts/setup_client.py")
        print()
        print("Y cuando te pida el nombre del cliente, introduce:")
        print("  Patacones de mi tierra")
        print()
        print("El script detectará que ya existe y solo creará el administrador.")
        print()

    sys.exit(0 if success else 1)
