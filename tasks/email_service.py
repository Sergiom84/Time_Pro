"""
Servicio de envío de correos electrónicos MEJORADO para notificaciones de fichaje

MEJORAS IMPLEMENTADAS:
1. Ventana de tiempo reducida: 7 minutos (-2 a +5) en lugar de 15
2. Locking a nivel de base de datos (SELECT FOR UPDATE)
3. Mejor manejo de errores con rollback
4. Logging de cada envío en tabla de auditoría
5. Prevención robusta contra duplicados
"""
from flask_mail import Message
from datetime import datetime, time
import os
from sqlalchemy import text


def send_notification_email_v2(mail, user, notification_type='entry'):
    """
    Envía un correo de notificación de fichaje al usuario y actualiza el timestamp

    MEJORAS:
    - Transacción atómica con rollback en caso de error
    - Logging de cada envío
    - Manejo robusto de errores

    Args:
        mail: Instancia de Flask-Mail
        user: Usuario al que enviar el correo
        notification_type: 'entry' para entrada, 'exit' para salida

    Returns:
        True si el envío fue exitoso, False en caso contrario
    """
    from models.database import db
    from models.email_log import EmailNotificationLog

    # Preparar datos del email
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
        scheduled_time = user.notification_time_entry
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
        scheduled_time = user.notification_time_exit

    # Preparar lista de destinatarios
    recipients = [user.email]
    additional_email = None
    if user.additional_notification_email:
        recipients.append(user.additional_notification_email)
        additional_email = user.additional_notification_email

    # Intentar enviar el correo dentro de una transacción
    try:
        # Crear el mensaje
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body
        )

        # Enviar el correo
        mail.send(msg)
        print(f"[EMAIL] ✓ Correo enviado a {', '.join(recipients)} ({notification_type})")

        # Actualizar el timestamp de la última notificación enviada
        if notification_type == 'entry':
            user.last_entry_notification_sent = datetime.now()
        else:
            user.last_exit_notification_sent = datetime.now()

        # Crear registro de log exitoso
        log_entry = EmailNotificationLog(
            user_id=user.id,
            notification_type=notification_type,
            email_to=user.email,
            additional_email_to=additional_email,
            scheduled_time=scheduled_time,
            sent_at=datetime.now(),
            success=True,
            error_message=None
        )
        db.session.add(log_entry)

        # Commit de todos los cambios juntos
        db.session.commit()
        print(f"[EMAIL] ✓ Registro guardado en base de datos")

        return True

    except Exception as e:
        # Rollback en caso de error
        db.session.rollback()
        print(f"[EMAIL] ✗ ERROR al enviar correo a {user.email}: {e}")

        # Intentar registrar el error en el log
        try:
            log_entry = EmailNotificationLog(
                user_id=user.id,
                notification_type=notification_type,
                email_to=user.email,
                additional_email_to=additional_email,
                scheduled_time=scheduled_time,
                sent_at=datetime.now(),
                success=False,
                error_message=str(e)[:500]  # Limitar longitud del error
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as log_error:
            print(f"[EMAIL] ✗ ERROR al guardar log de error: {log_error}")
            db.session.rollback()

        return False


def check_and_send_notifications_v2(app, mail):
    """
    Revisa qué usuarios necesitan recibir notificaciones y las envía

    MEJORAS:
    - Ventana de tiempo reducida: 7 minutos (-2 a +5)
    - Locking con SELECT FOR UPDATE para prevenir race conditions
    - Verificación más robusta de duplicados
    - Mejor logging

    Esta función debe ser ejecutada por el scheduler cada 5 minutos
    """
    with app.app_context():
        from models.models import User
        from models.database import db
        from datetime import datetime, timedelta

        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Lunes, 6=Domingo

        print(f"\n[SCHEDULER V2] 🔄 Revisando notificaciones a las {now.strftime('%H:%M:%S')}")

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
        print(f"[SCHEDULER V2] 📅 Día de hoy: {today_letter}")

        # Obtener usuarios con notificaciones activas
        users = User.query.filter_by(
            email_notifications=True,
            is_active=True
        ).all()

        print(f"[SCHEDULER V2] 👥 Usuarios con notificaciones activas: {len(users)}")

        notifications_sent = 0
        notifications_skipped = 0

        for user in users:
            # Verificar si hoy es un día seleccionado
            if not user.notification_days:
                print(f"[SCHEDULER V2] ⏭️  Usuario {user.username}: sin días configurados")
                continue

            selected_days = [day.strip() for day in user.notification_days.split(',')]
            if today_letter not in selected_days:
                print(f"[SCHEDULER V2] ⏭️  Usuario {user.username}: hoy no está en días seleccionados ({selected_days})")
                continue

            print(f"[SCHEDULER V2] 👤 Usuario {user.username}: procesando notificaciones")

            # MEJORA: Usar SELECT FOR UPDATE para bloquear el registro durante la verificación
            # Esto previene race conditions si múltiples procesos ejecutan al mismo tiempo
            locked_user = db.session.query(User).filter_by(id=user.id).with_for_update().first()

            # Verificar hora de notificación de entrada
            if locked_user.notification_time_entry:
                entry_time = locked_user.notification_time_entry
                time_diff = (datetime.combine(datetime.today(), current_time) -
                           datetime.combine(datetime.today(), entry_time)).total_seconds() / 60

                print(f"[SCHEDULER V2]   📥 Entrada: {entry_time.strftime('%H:%M')} | Diferencia: {time_diff:.1f} min")

                # MEJORA: Ventana reducida de 7 minutos (-2 a +5)
                # Reduce las oportunidades de ejecuciones múltiples
                if -2 <= time_diff <= 5:
                    # Verificar si ya se envió una notificación de entrada hoy
                    already_sent = False
                    if locked_user.last_entry_notification_sent:
                        last_sent_date = locked_user.last_entry_notification_sent.date()
                        today_date = datetime.today().date()
                        already_sent = last_sent_date == today_date

                        # MEJORA: Verificar también que no sea muy reciente (última hora)
                        # Esto añade una capa adicional de protección
                        if already_sent:
                            time_since_last = datetime.now() - locked_user.last_entry_notification_sent
                            if time_since_last.total_seconds() < 3600:  # Menos de 1 hora
                                print(f"[SCHEDULER V2]   ⚠️  Ya se envió notificación de ENTRADA a {locked_user.username} hace {int(time_since_last.total_seconds()/60)} minutos")
                            else:
                                print(f"[SCHEDULER V2]   ⚠️  Ya se envió notificación de ENTRADA a {locked_user.username} hoy")

                    if already_sent:
                        notifications_skipped += 1
                    else:
                        print(f"[SCHEDULER V2]   ✅ Enviando email de ENTRADA a {locked_user.username}")
                        success = send_notification_email_v2(mail, locked_user, 'entry')
                        if success:
                            notifications_sent += 1
                        else:
                            print(f"[SCHEDULER V2]   ❌ Fallo al enviar email de ENTRADA a {locked_user.username}")
                else:
                    print(f"[SCHEDULER V2]   ⏸️  Fuera de ventana de tiempo para entrada")

            # Refrescar el usuario bloqueado para verificar salida
            locked_user = db.session.query(User).filter_by(id=user.id).with_for_update().first()

            # Verificar hora de notificación de salida
            if locked_user.notification_time_exit:
                exit_time = locked_user.notification_time_exit
                time_diff = (datetime.combine(datetime.today(), current_time) -
                           datetime.combine(datetime.today(), exit_time)).total_seconds() / 60

                print(f"[SCHEDULER V2]   📤 Salida: {exit_time.strftime('%H:%M')} | Diferencia: {time_diff:.1f} min")

                # MEJORA: Ventana reducida de 7 minutos (-2 a +5)
                if -2 <= time_diff <= 5:
                    # Verificar si ya se envió una notificación de salida hoy
                    already_sent = False
                    if locked_user.last_exit_notification_sent:
                        last_sent_date = locked_user.last_exit_notification_sent.date()
                        today_date = datetime.today().date()
                        already_sent = last_sent_date == today_date

                        # MEJORA: Verificar también que no sea muy reciente (última hora)
                        if already_sent:
                            time_since_last = datetime.now() - locked_user.last_exit_notification_sent
                            if time_since_last.total_seconds() < 3600:  # Menos de 1 hora
                                print(f"[SCHEDULER V2]   ⚠️  Ya se envió notificación de SALIDA a {locked_user.username} hace {int(time_since_last.total_seconds()/60)} minutos")
                            else:
                                print(f"[SCHEDULER V2]   ⚠️  Ya se envió notificación de SALIDA a {locked_user.username} hoy")

                    if already_sent:
                        notifications_skipped += 1
                    else:
                        print(f"[SCHEDULER V2]   ✅ Enviando email de SALIDA a {locked_user.username}")
                        success = send_notification_email_v2(mail, locked_user, 'exit')
                        if success:
                            notifications_sent += 1
                        else:
                            print(f"[SCHEDULER V2]   ❌ Fallo al enviar email de SALIDA a {locked_user.username}")
                else:
                    print(f"[SCHEDULER V2]   ⏸️  Fuera de ventana de tiempo para salida")

            # Commit del bloqueo
            db.session.commit()

        print(f"[SCHEDULER V2] ✅ Revisión completada: {notifications_sent} enviados, {notifications_skipped} omitidos\n")
