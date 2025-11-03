"""
Servicio de envío de correos electrónicos para notificaciones de fichaje
"""
from flask_mail import Message
from datetime import datetime, time
import os


def send_notification_email(mail, user, notification_type='entry'):
    """
    Envía un correo de notificación de fichaje al usuario

    Args:
        mail: Instancia de Flask-Mail
        user: Usuario al que enviar el correo
        notification_type: 'entry' para entrada, 'exit' para salida
    """
    try:
        if notification_type == 'entry':
            subject = '⏰ Recordatorio de Fichaje de Entrada'
            body = f"""
Hola {user.full_name},

Este es un recordatorio para que no olvides fichar tu entrada.

Centro: {user.centro or 'No asignado'}

Puedes fichar desde el panel de empleado en: {os.getenv('APP_URL', 'tu aplicación')}

¡Que tengas un buen día!

---
Time Tracker - Sistema de Control de Fichajes
            """
        else:  # exit
            subject = '⏰ Recordatorio de Fichaje de Salida'
            body = f"""
Hola {user.full_name},

Este es un recordatorio para que no olvides fichar tu salida.

Centro: {user.centro or 'No asignado'}

Puedes fichar desde el panel de empleado en: {os.getenv('APP_URL', 'tu aplicación')}

¡Hasta mañana!

---
Time Tracker - Sistema de Control de Fichajes
            """

        # Preparar lista de destinatarios
        recipients = [user.email]
        if user.additional_notification_email:
            recipients.append(user.additional_notification_email)

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body
        )

        mail.send(msg)
        print(f"[EMAIL] Correo enviado a {', '.join(recipients)} ({notification_type})")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Error al enviar correo a {user.email}: {e}")
        return False


def check_and_send_notifications(app, mail):
    """
    Revisa qué usuarios necesitan recibir notificaciones y las envía
    Esta función debe ser ejecutada por el scheduler cada X minutos
    """
    with app.app_context():
        from models.models import User
        from datetime import datetime, timedelta

        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Lunes, 6=Domingo

        print(f"\n[SCHEDULER] Revisando notificaciones a las {now.strftime('%H:%M:%S')}")

        # Mapeo de días
        weekday_map = {
            0: 'L',  # Lunes
            1: 'M',  # Martes
            2: 'X',  # Miércoles
            3: 'J',  # Jueves
            4: 'V',  # Viernes
            5: 'S',  # Sábado
            6: 'D'   # Domingo
        }

        today_letter = weekday_map.get(current_weekday)
        print(f"[SCHEDULER] Día de hoy: {today_letter}")

        # Obtener usuarios con notificaciones activas
        users = User.query.filter_by(
            email_notifications=True,
            is_active=True
        ).all()

        print(f"[SCHEDULER] Usuarios con notificaciones activas: {len(users)}")

        for user in users:
            # Verificar si hoy es un día seleccionado
            if not user.notification_days:
                print(f"[SCHEDULER] Usuario {user.username}: sin días configurados")
                continue

            selected_days = [day.strip() for day in user.notification_days.split(',')]
            if today_letter not in selected_days:
                print(f"[SCHEDULER] Usuario {user.username}: hoy no está en días seleccionados ({selected_days})")
                continue

            print(f"[SCHEDULER] Usuario {user.username}: procesando notificaciones")

            # Verificar hora de notificación de entrada
            if user.notification_time_entry:
                entry_time = user.notification_time_entry
                time_diff = (datetime.combine(datetime.today(), current_time) -
                           datetime.combine(datetime.today(), entry_time)).total_seconds() / 60

                print(f"[SCHEDULER]   Entrada: {entry_time.strftime('%H:%M')} | Diferencia: {time_diff:.1f} min")

                # Ventana ampliada: 5 minutos antes hasta 10 minutos después
                if -5 <= time_diff <= 10:
                    print(f"[SCHEDULER]   ✓ Enviando email de ENTRADA a {user.username}")
                    send_notification_email(mail, user, 'entry')

            # Verificar hora de notificación de salida
            if user.notification_time_exit:
                exit_time = user.notification_time_exit
                time_diff = (datetime.combine(datetime.today(), current_time) -
                           datetime.combine(datetime.today(), exit_time)).total_seconds() / 60

                print(f"[SCHEDULER]   Salida: {exit_time.strftime('%H:%M')} | Diferencia: {time_diff:.1f} min")

                # Ventana ampliada: 5 minutos antes hasta 10 minutos después
                if -5 <= time_diff <= 10:
                    print(f"[SCHEDULER]   ✓ Enviando email de SALIDA a {user.username}")
                    send_notification_email(mail, user, 'exit')

        print(f"[SCHEDULER] Revisión completada\n")
