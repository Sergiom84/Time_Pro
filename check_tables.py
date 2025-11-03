"""
Script para verificar las tablas existentes en la base de datos
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

def check_tables():
    """Verifica las tablas existentes en la base de datos"""
    try:
        print("Conectando a la base de datos...")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        print("\nObteniendo lista de tablas...")
        sql = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
        """

        cursor.execute(sql)
        tables = cursor.fetchall()

        print(f"\n{'Schema':<20} {'Tabla':<30}")
        print("=" * 50)
        for schema, table in tables:
            print(f"{schema:<20} {table:<30}")

        # Verificar columnas de la tabla users si existe
        print("\n\nVerificando columnas de la tabla 'users' en schema public...")
        sql_columns = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users'
        ORDER BY ordinal_position;
        """

        cursor.execute(sql_columns)
        columns = cursor.fetchall()

        if columns:
            print(f"\n{'Columna':<40} {'Tipo':<20} {'Long':<10}")
            print("=" * 70)
            for col, dtype, length in columns:
                length_str = str(length) if length else "-"
                print(f"{col:<40} {dtype:<20} {length_str:<10}")
        else:
            print("No se encontro la tabla 'users' en el schema 'public'")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables()
