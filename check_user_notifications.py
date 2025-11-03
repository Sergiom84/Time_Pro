"""
Script simple para verificar la configuración de notificaciones
"""
import psycopg2
from urllib.parse import quote_plus
from datetime import datetime

# Configuración de Supabase
supabase_password = "OPt0u_oag6Pir5MR0@"
supabase_password_encoded = quote_plus(supabase_password)

conn_string = (
    f"postgresql://postgres.gqesfclbingbihakiojm:"
    f"{supabase_password_encoded}@"
    f"aws-1-eu-west-1.pooler.supabase.com:6543/"
    f"postgres"
)

def check_user_settings():
    """Verifica la configuración del usuario Emcentro2"""
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Buscar usuario Emcentro2
        cursor.execute("""
            SELECT username, email, email_notifications, notification_days,
                   notification_time_entry, notification_time_exit,
                   additional_notification_email, is_active
            FROM "user"
            WHERE username = 'Empleado2'
        """)

        user = cursor.fetchone()

        if not user:
            print("Usuario 'Emcentro2' no encontrado")
            return

        username, email, email_notif, notif_days, time_entry, time_exit, additional_email, is_active = user

        print("=" * 70)
        print("CONFIGURACION DEL USUARIO")
        print("=" * 70)
        print(f"Usuario: {username}")
        print(f"Email principal: {email}")
        print(f"Email adicional: {additional_email or 'No configurado'}")
        print(f"Notificaciones activas: {email_notif}")
        print(f"Usuario activo: {is_active}")
        print(f"Dias seleccionados: {notif_days}")
        print(f"Hora de entrada: {time_entry}")
        print(f"Hora de salida: {time_exit}")
        print("=" * 70)

        # Verificar si hoy es un día válido
        now = datetime.now()
        current_weekday = now.weekday()
        weekday_map = {0: 'L', 1: 'M', 2: 'X', 3: 'J', 4: 'V', 5: 'S', 6: 'D'}
        today_letter = weekday_map.get(current_weekday)

        print(f"\nHora actual: {now.strftime('%A, %d/%m/%Y %H:%M:%S')}")
        print(f"Letra del dia (0=L, 6=D): {today_letter}")

        if notif_days:
            selected_days = [day.strip() for day in notif_days.split(',')]
            print(f"Dias configurados: {selected_days}")
            print(f"Hoy esta incluido?: {'SI' if today_letter in selected_days else 'NO'}")

        # Calcular diferencia de tiempo con la hora de salida
        if time_exit:
            current_time = now.time()
            time_diff = (datetime.combine(datetime.today(), current_time) -
                        datetime.combine(datetime.today(), time_exit)).total_seconds() / 60

            print(f"\n--- ANALISIS DE VENTANA DE TIEMPO ---")
            print(f"Hora actual: {current_time.strftime('%H:%M:%S')}")
            print(f"Hora de salida configurada: {time_exit.strftime('%H:%M:%S')}")
            print(f"Diferencia en minutos: {time_diff:.2f}")
            print(f"Ventana de envio actual (-5 a +10 min): {-5 <= time_diff <= 10}")

            if time_diff < -5:
                print(f"  -> Aun faltan {abs(time_diff + 5):.1f} minutos para entrar en la ventana")
            elif time_diff > 10:
                print(f"  -> La ventana cerro hace {time_diff - 10:.1f} minutos")
            else:
                print(f"  -> DENTRO DE LA VENTANA - Se deberia enviar el correo!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user_settings()
