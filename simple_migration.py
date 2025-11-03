"""
Script simple para aplicar la migración del campo additional_notification_email
Sin dependencias de la aplicación completa
"""
import psycopg2
from urllib.parse import quote_plus

# Configuración de Supabase
supabase_password = "OPt0u_oag6Pir5MR0@"
supabase_password_encoded = quote_plus(supabase_password)

# Construir cadena de conexión
conn_string = (
    f"postgresql://postgres.gqesfclbingbihakiojm:"
    f"{supabase_password_encoded}@"
    f"aws-1-eu-west-1.pooler.supabase.com:6543/"
    f"postgres"
)

def apply_migration():
    """Aplica la migración para agregar el campo additional_notification_email"""
    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        print("Aplicando migracion...")
        sql = """
        ALTER TABLE "user"
        ADD COLUMN IF NOT EXISTS additional_notification_email VARCHAR(120);
        """

        cursor.execute(sql)
        conn.commit()

        print("Migracion aplicada exitosamente")
        print("   Campo 'additional_notification_email' agregado a la tabla user")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error al aplicar la migracion: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    apply_migration()
