"""
Script para aplicar la migración del campo additional_notification_email
"""
import os
import sys
from urllib.parse import quote_plus

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db

def apply_migration():
    """Aplica la migración para agregar el campo additional_notification_email"""
    with app.app_context():
        try:
            # Ejecutar la migración SQL
            sql = """
            ALTER TABLE users ADD COLUMN IF NOT EXISTS additional_notification_email VARCHAR(120);
            """

            db.session.execute(db.text(sql))
            db.session.commit()

            print("✅ Migración aplicada exitosamente")
            print("   Campo 'additional_notification_email' agregado a la tabla users")

        except Exception as e:
            print(f"❌ Error al aplicar la migración: {e}")
            db.session.rollback()

if __name__ == "__main__":
    apply_migration()
