"""
Script para aplicar las migraciones necesarias para la actualización del sistema de solicitudes:
1. Añadir nuevos estados al enum request_status_enum
2. Añadir campos de seguimiento de lectura
3. Actualizar solicitudes existentes según su tipo
"""

from models.database import db
from models.models import LeaveRequest
from sqlalchemy import text
from datetime import datetime
import os
from main import app

def apply_migration():
    """Aplica las migraciones necesarias para el sistema de solicitudes"""

    with app.app_context():
        try:
            print("🔄 Iniciando migración del sistema de solicitudes...")

            # Verificar si los campos ya existen
            result = db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'leave_request' AND column_name = 'read_by_admin'")
            )
            if result.fetchone():
                print("✅ Los campos ya existen en la base de datos. No se requiere migración.")
                return

            print("\n📝 Paso 1: Actualizando enum de estados...")

            # Primero guardamos cualquier dato actual
            db.session.execute(text("BEGIN"))

            # Crear un tipo temporal con los nuevos valores
            db.session.execute(text("""
                DO $$
                BEGIN
                    -- Crear nuevo enum si no existe
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'request_status_enum_temp') THEN
                        CREATE TYPE request_status_enum_temp AS ENUM (
                            'Pendiente', 'Aprobado', 'Rechazado', 'Cancelado', 'Enviado', 'Recibido'
                        );
                    END IF;
                END$$;
            """))

            # Actualizar la columna para usar el nuevo enum
            # Primero quitamos el valor por defecto
            db.session.execute(text("ALTER TABLE leave_request ALTER COLUMN status DROP DEFAULT"))

            # Actualizar el tipo
            db.session.execute(text("""
                ALTER TABLE leave_request
                ALTER COLUMN status TYPE request_status_enum_temp
                USING status::text::request_status_enum_temp
            """))

            # Restaurar el valor por defecto
            db.session.execute(text("ALTER TABLE leave_request ALTER COLUMN status SET DEFAULT 'Pendiente'"))

            # Eliminar el enum antiguo y renombrar el nuevo
            db.session.execute(text("DROP TYPE IF EXISTS request_status_enum CASCADE"))
            db.session.execute(text("ALTER TYPE request_status_enum_temp RENAME TO request_status_enum"))

            print("✅ Enum de estados actualizado")

            print("\n📝 Paso 2: Añadiendo campos de seguimiento de lectura...")

            # Añadir nuevos campos
            db.session.execute(text("""
                ALTER TABLE leave_request
                ADD COLUMN IF NOT EXISTS read_by_admin BOOLEAN DEFAULT FALSE NOT NULL,
                ADD COLUMN IF NOT EXISTS read_date TIMESTAMP
            """))

            print("✅ Campos de lectura añadidos")

            print("\n📝 Paso 3: Actualizando estados de solicitudes existentes...")

            # Actualizar solicitudes de bajas y ausencias que estén en 'Pendiente' a 'Enviado'
            result = db.session.execute(text("""
                UPDATE leave_request
                SET status = 'Enviado'
                WHERE request_type IN ('Baja médica', 'Ausencia justificada', 'Ausencia injustificada')
                  AND status = 'Pendiente'
                RETURNING id
            """))

            updated_count = result.rowcount
            print(f"✅ {updated_count} solicitudes actualizadas a estado 'Enviado'")

            # Marcar como leídas las solicitudes ya procesadas
            result = db.session.execute(text("""
                UPDATE leave_request
                SET read_by_admin = TRUE,
                    read_date = approval_date
                WHERE status IN ('Aprobado', 'Rechazado')
                  AND read_by_admin = FALSE
                RETURNING id
            """))

            read_count = result.rowcount
            print(f"✅ {read_count} solicitudes marcadas como leídas")

            # Confirmar los cambios
            db.session.commit()

            print("\n✅ ¡Migración completada exitosamente!")
            print("\nCambios aplicados:")
            print("- Nuevos estados: 'Enviado' y 'Recibido' añadidos")
            print("- Campos de seguimiento de lectura añadidos")
            print("- Solicitudes existentes actualizadas según su tipo")
            print("\nEl sistema ahora maneja los estados de la siguiente manera:")
            print("  • Vacaciones: Pendiente → Aprobado/Rechazado")
            print("  • Bajas y Ausencias: Enviado → Recibido")

        except Exception as e:
            print(f"\n❌ Error durante la migración: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    apply_migration()