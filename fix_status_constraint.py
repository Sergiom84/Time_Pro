"""
Script para actualizar el CHECK constraint de status en leave_request
"""
from sqlalchemy import text
from models.database import db
from main import app

with app.app_context():
    try:
        print("🔧 Actualizando CHECK constraint de status...")

        # Eliminar el constraint antiguo
        db.session.execute(text("""
            ALTER TABLE leave_request
            DROP CONSTRAINT IF EXISTS leave_request_status_check;
        """))

        print("✅ Constraint antiguo eliminado")

        # Crear nuevo constraint con todos los valores
        db.session.execute(text("""
            ALTER TABLE leave_request
            ADD CONSTRAINT leave_request_status_check
            CHECK (status::text = ANY (ARRAY[
                'Pendiente'::text,
                'Aprobado'::text,
                'Rechazado'::text,
                'Cancelado'::text,
                'Enviado'::text,
                'Recibido'::text
            ]));
        """))

        print("✅ Nuevo constraint creado con los valores:")
        print("   - Pendiente")
        print("   - Aprobado")
        print("   - Rechazado")
        print("   - Cancelado")
        print("   - Enviado (NUEVO)")
        print("   - Recibido (NUEVO)")

        db.session.commit()
        print("\n✅ Cambios aplicados correctamente")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
