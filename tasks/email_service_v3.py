"""
Servicio de envío de correos electrónicos V3 - CON LOCK DISTRIBUIDO

MEJORA V3:
- Añade lock distribuido a nivel de base de datos
- Previene que múltiples workers/procesos ejecuten el scheduler simultáneamente
- Usa PostgreSQL advisory locks
"""
from flask_mail import Message
from datetime import datetime, time
import os
from sqlalchemy import text


def send_notification_email_v3(mail, user, notification_type='entry'):
    """
    Envía un correo de notificación de fichaje al usuario y actualiza el timestamp

    MEJORAS V3:
    - Igual que V2, pero se usa junto con el lock distribuido

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
        print(f"[EMAIL V3] ✓ Correo enviado a {', '.join(recipients)} ({notification_type})")

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
        print(f"[EMAIL V3] ✓ Registro guardado en base de datos")

        return True

    except Exception as e:
        # Rollback en caso de error
        db.session.rollback()
        print(f"[EMAIL V3] ✗ ERROR al enviar correo a {user.email}: {e}")

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
                error_message=str(e)[:500]
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as log_error:
            print(f"[EMAIL V3] ✗ ERROR al guardar log de error: {log_error}")
            db.session.rollback()

        return False


def check_and_send_notifications_v3(app, mail):
    """
    Revisa qué usuarios necesitan recibir notificaciones y las envía

    MEJORA V3: LOCK DISTRIBUIDO
    - Usa PostgreSQL advisory lock para garantizar que solo un proceso ejecuta a la vez
    - Si otro proceso ya está ejecutando, este proceso sale inmediatamente
    - Previene duplicados cuando hay múltiples workers

    Lock ID usado: 123456789 (número arbitrario único para esta función)
    """
    with app.app_context():
        from models.models import User
        from models.database import db
        from datetime import datetime, timedelta

        # LOCK ID único para esta función
        LOCK_ID = 123456789

        try:
            # Intentar obtener lock NO BLOQUEANTE (pg_try_advisory_lock)
            # Si otro proceso ya tiene el lock, retorna False y salimos
            result = db.session.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": LOCK_ID}
            ).scalar()

            if not result:
                print(f"[SCHEDULER V3] 🔒 Otro proceso ya está ejecutando el scheduler. Saliendo...")
                return

            print(f"[SCHEDULER V3] 🔓 Lock obtenido. Procesando notificaciones...")

            # A partir de aquí, tenemos el lock exclusivo
            now = datetime.now()
            current_time = now.time()
            current_weekday = now.weekday()

            print(f"[SCHEDULER V3] 🔄 Revisando notificaciones a las {now.strftime('%H:%M:%S')}")

            # Mapeo de días
            weekday_map = {
                0: 'L', 1: 'M', 2: 'X', 3: 'J',
                4: 'V', 5: 'S', 6: 'D'
            }

            today_letter = weekday_map.get(current_weekday)
            print(f"[SCHEDULER V3] 📅 Día de hoy: {today_letter}")

            # Obtener usuarios con notificaciones activas
            users = User.query.filter_by(
                email_notifications=True,
                is_active=True
            ).all()

            print(f"[SCHEDULER V3] 👥 Usuarios con notificaciones activas: {len(users)}")

            notifications_sent = 0
            notifications_skipped = 0

            for user in users:
                # Verificar si hoy es un día seleccionado
                if not user.notification_days:
                    print(f"[SCHEDULER V3] ⏭️  Usuario {user.username}: sin días configurados")
                    continue

                selected_days = [day.strip() for day in user.notification_days.split(',')]
                if today_letter not in selected_days:
                    print(f"[SCHEDULER V3] ⏭️  Usuario {user.username}: hoy no está en días seleccionados ({selected_days})")
                    continue

                print(f"[SCHEDULER V3] 👤 Usuario {user.username}: procesando notificaciones")

                # Usar SELECT FOR UPDATE para bloquear el registro
                locked_user = db.session.query(User).filter_by(id=user.id).with_for_update().first()

                # Verificar hora de notificación de entrada
                if locked_user.notification_time_entry:
                    entry_time = locked_user.notification_time_entry
                    time_diff = (datetime.combine(datetime.today(), current_time) -
                               datetime.combine(datetime.today(), entry_time)).total_seconds() / 60

                    print(f"[SCHEDULER V3]   📥 Entrada: {entry_time.strftime('%H:%M')} | Diferencia: {time_diff:.1f} min")

                    # Ventana reducida: -2 a +5 minutos
                    if -2 <= time_diff <= 5:
                        # Verificar si ya se envió una notificación de entrada hoy
                        already_sent = False
                        if locked_user.last_entry_notification_sent:
                            last_sent_date = locked_user.last_entry_notification_sent.date()
                            today_date = datetime.today().date()
                            already_sent = last_sent_date == today_date

                            if already_sent:
                                time_since_last = datetime.now() - locked_user.last_entry_notification_sent
                                if time_since_last.total_seconds() < 3600:
                                    print(f"[SCHEDULER V3]   ⚠️  Ya se envió notificación de ENTRADA a {locked_user.username} hace {int(time_since_last.total_seconds()/60)} minutos")
                                else:
                                    print(f"[SCHEDULER V3]   ⚠️  Ya se envió notificación de ENTRADA a {locked_user.username} hoy")

                        if already_sent:
                            notifications_skipped += 1
                        else:
                            print(f"[SCHEDULER V3]   ✅ Enviando email de ENTRADA a {locked_user.username}")
                            success = send_notification_email_v3(mail, locked_user, 'entry')
                            if success:
                                notifications_sent += 1
                            else:
                                print(f"[SCHEDULER V3]   ❌ Fallo al enviar email de ENTRADA a {locked_user.username}")
                    else:
                        print(f"[SCHEDULER V3]   ⏸️  Fuera de ventana de tiempo para entrada")

                # Refrescar el usuario bloqueado para verificar salida
                locked_user = db.session.query(User).filter_by(id=user.id).with_for_update().first()

                # Verificar hora de notificación de salida
                if locked_user.notification_time_exit:
                    exit_time = locked_user.notification_time_exit
                    time_diff = (datetime.combine(datetime.today(), current_time) -
                               datetime.combine(datetime.today(), exit_time)).total_seconds() / 60

                    print(f"[SCHEDULER V3]   📤 Salida: {exit_time.strftime('%H:%M')} | Diferencia: {time_diff:.1f} min")

                    # Ventana reducida: -2 a +5 minutos
                    if -2 <= time_diff <= 5:
                        # Verificar si ya se envió una notificación de salida hoy
                        already_sent = False
                        if locked_user.last_exit_notification_sent:
                            last_sent_date = locked_user.last_exit_notification_sent.date()
                            today_date = datetime.today().date()
                            already_sent = last_sent_date == today_date

                            if already_sent:
                                time_since_last = datetime.now() - locked_user.last_exit_notification_sent
                                if time_since_last.total_seconds() < 3600:
                                    print(f"[SCHEDULER V3]   ⚠️  Ya se envió notificación de SALIDA a {locked_user.username} hace {int(time_since_last.total_seconds()/60)} minutos")
                                else:
                                    print(f"[SCHEDULER V3]   ⚠️  Ya se envió notificación de SALIDA a {locked_user.username} hoy")

                        if already_sent:
                            notifications_skipped += 1
                        else:
                            print(f"[SCHEDULER V3]   ✅ Enviando email de SALIDA a {locked_user.username}")
                            success = send_notification_email_v3(mail, locked_user, 'exit')
                            if success:
                                notifications_sent += 1
                            else:
                                print(f"[SCHEDULER V3]   ❌ Fallo al enviar email de SALIDA a {locked_user.username}")
                    else:
                        print(f"[SCHEDULER V3]   ⏸️  Fuera de ventana de tiempo para salida")

                # Commit del bloqueo
                db.session.commit()

            print(f"[SCHEDULER V3] ✅ Revisión completada: {notifications_sent} enviados, {notifications_skipped} omitidos")

        finally:
            # IMPORTANTE: Liberar el lock al finalizar (con o sin error)
            try:
                db.session.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": LOCK_ID}
                )
                print(f"[SCHEDULER V3] 🔓 Lock liberado\n")
            except Exception as e:
                print(f"[SCHEDULER V3] ⚠️  Error al liberar lock: {e}\n")
