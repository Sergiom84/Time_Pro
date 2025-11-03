"""
Script para verificar constraints de la tabla leave_request
"""
from sqlalchemy import text
from models.database import db
from main import app

with app.app_context():
    try:
        # Consultar constraints de la tabla
        result = db.session.execute(text("""
            SELECT
                conname AS constraint_name,
                pg_get_constraintdef(c.oid) AS constraint_definition
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE conrelid = 'leave_request'::regclass
            AND contype = 'c'  -- CHECK constraints
            ORDER BY conname;
        """))

        constraints = list(result)

        print("📋 CHECK Constraints en leave_request:")
        for constraint in constraints:
            print(f"\n   Nombre: {constraint[0]}")
            print(f"   Definición: {constraint[1]}")

        if not constraints:
            print("   No se encontraron CHECK constraints")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
