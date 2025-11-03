"""
Script para verificar los valores del enum request_status_enum en la BD
"""
from sqlalchemy import text
from models.database import db
from main import app

with app.app_context():
    try:
        # Consultar los valores del enum
        result = db.session.execute(text("""
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (
                SELECT oid
                FROM pg_type
                WHERE typname = 'request_status_enum'
            )
            ORDER BY enumsortorder;
        """))

        valores = [row[0] for row in result]

        print("📋 Valores actuales en request_status_enum:")
        for valor in valores:
            print(f"   - {valor}")

        # Verificar si existen los nuevos estados
        estados_requeridos = ["Enviado", "Recibido"]
        faltantes = [e for e in estados_requeridos if e not in valores]

        if faltantes:
            print(f"\n⚠️  Estados faltantes: {', '.join(faltantes)}")
            print("   Necesitas ejecutar la migración.")
        else:
            print("\n✅ Todos los estados requeridos están presentes")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
