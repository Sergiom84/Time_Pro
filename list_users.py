"""
Script para listar todos los usuarios
"""
import psycopg2
from urllib.parse import quote_plus

# Configuración de Supabase
supabase_password = "OPt0u_oag6Pir5MR0@"
supabase_password_encoded = quote_plus(supabase_password)

conn_string = (
    f"postgresql://postgres.gqesfclbingbihakiojm:"
    f"{supabase_password_encoded}@"
    f"aws-1-eu-west-1.pooler.supabase.com:6543/"
    f"postgres"
)

def list_users():
    """Lista todos los usuarios"""
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, email, email_notifications, is_active
            FROM "user"
            ORDER BY username
        """)

        users = cursor.fetchall()

        print("=" * 80)
        print(f"TOTAL DE USUARIOS: {len(users)}")
        print("=" * 80)
        print(f"{'Username':<25} {'Email':<35} {'Notif':<8} {'Activo':<8}")
        print("-" * 80)

        for username, email, email_notif, is_active in users:
            print(f"{username:<25} {email:<35} {str(email_notif):<8} {str(is_active):<8}")

        print("=" * 80)

        # Buscar usuarios con notificaciones activas
        cursor.execute("""
            SELECT username, email, notification_time_exit
            FROM "user"
            WHERE email_notifications = true AND is_active = true
        """)

        notif_users = cursor.fetchall()

        print(f"\nUSUARIOS CON NOTIFICACIONES ACTIVAS: {len(notif_users)}")
        for username, email, time_exit in notif_users:
            print(f"  - {username}: {email} | Salida: {time_exit}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    list_users()
