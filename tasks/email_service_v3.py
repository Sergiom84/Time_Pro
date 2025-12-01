"""
Servicio de envío de correos electrónicos V3 - CON LOCK DISTRIBUIDO

MEJORA V3:
- Añade lock distribuido a nivel de base de datos
- Previene que múltiples workers/procesos ejecuten el scheduler simultáneamente
- Usa PostgreSQL advisory locks
"""

from datetime import datetime, time
import os

from flask_mail import Message
from sqlalchemy import text

from utils.logging_utils import get_logger

logger = get_logger(__name__)


def send_notification_email_v3(mail, user, notification_type: str = "entry") -> bool:
    """
    Envía un correo de notificación de fichaje al usuario y actualiza el timestamp.

    Args:
        mail: Instancia de Flask-Mail
        user: Usuario al que enviar el correo
        notification_type: 'entry' para entrada, 'exit' para salida

    Returns:
        True si el envío fue exitoso, False en caso contrario
    """
    from models.database import db
    from models.email_log import EmailNotificationLog

    if notification_type == "entry":
        subject = "⏰ Recordatorio de Fichaje de Entrada"
        body = f"""
Hola {user.full_name},

Este es un recordatorio para que no olvides fichar tu entrada.

Centro: {user.center.name if user.center else 'No asignado'}

Puedes fichar desde el panel de empleado en: {os.getenv('APP_URL', 'tu aplicación')}

¡Que tengas un buen día!

---
Time Tracker - Sistema de Control de Fichajes
        """
        scheduled_time = user.notification_time_entry
    else:
        subject = "⏰ Recordatorio de Fichaje de Salida"
        body = f"""
Hola {user.full_name},

Este es un recordatorio para que no olvides fichar tu salida.

Centro: {user.center.name if user.center else 'No asignado'}

Puedes fichar desde el panel de empleado en: {os.getenv('APP_URL', 'tu aplicación')}

¡Hasta mañana!

---
Time Tracker - Sistema de Control de Fichajes
        """
        scheduled_time = user.notification_time_exit

    recipients = [user.email]
    additional_email = None
    if user.additional_notification_email:
        recipients.append(user.additional_notification_email)
        additional_email = user.additional_notification_email

    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
        logger.info("[EMAIL V3] Correo enviado a %s (%s)", ", ".join(recipients), notification_type)

        # Actualizar marcas de último envío
        now = datetime.now()
        if notification_type == "entry":
            user.last_entry_notification_sent = now
        else:
            user.last_exit_notification_sent = now

        log_entry = EmailNotificationLog(
            user_id=user.id,
            notification_type=notification_type,
            email_to=user.email,
            additional_email_to=additional_email,
            scheduled_time=scheduled_time,
            sent_at=now,
            success=True,
            error_message=None,
        )
        db.session.add(log_entry)
        db.session.commit()
        logger.debug("[EMAIL V3] Registro guardado en base de datos")
        return True

    except Exception as e:  # noqa: BLE001
        from models.database import db  # reimport para evitar problemas de contexto

        db.session.rollback()
        logger.error("[EMAIL V3] Error al enviar correo a %s: %s", user.email, e)

        try:
            from models.email_log import EmailNotificationLog

            log_entry = EmailNotificationLog(
                user_id=user.id,
                notification_type=notification_type,
                email_to=user.email,
                additional_email_to=additional_email,
                scheduled_time=scheduled_time,
                sent_at=datetime.now(),
                success=False,
                error_message=str(e)[:500],
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as log_error:  # noqa: BLE001
            db.session.rollback()
            logger.error("[EMAIL V3] Error al guardar log de error: %s", log_error)

        return False


def check_and_send_notifications_v3(app, mail) -> None:
    """
    Revisa qué usuarios necesitan recibir notificaciones y las envía.

    MEJORA V3: LOCK DISTRIBUIDO
    - Usa PostgreSQL advisory lock para garantizar que solo un proceso ejecuta a la vez
    - Si otro proceso ya está ejecutando, este proceso sale inmediatamente
    - Previene duplicados cuando hay múltiples workers
    """
    from models.models import User
    from models.database import db

    LOCK_ID = 123456789

    with app.app_context():
        try:
            # Intentar obtener lock NO BLOQUEANTE
            result = db.session.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": LOCK_ID}
            ).scalar()

            if not result:
                logger.info("[SCHEDULER V3] Otro proceso ya está ejecutando el scheduler. Saliendo...")
                return

            logger.info("[SCHEDULER V3] Lock obtenido. Procesando notificaciones...")

            now = datetime.now()
            current_time = now.time()
            current_weekday = now.weekday()
            logger.info(
                "[SCHEDULER V3] Revisando notificaciones a las %s",
                now.strftime("%H:%M:%S"),
            )

            weekday_map = {0: "L", 1: "M", 2: "X", 3: "J", 4: "V", 5: "S", 6: "D"}
            today_letter = weekday_map.get(current_weekday)
            logger.debug("[SCHEDULER V3] Día de hoy: %s", today_letter)

            users = User.query.filter_by(email_notifications=True, is_active=True).all()
            logger.info(
                "[SCHEDULER V3] Usuarios con notificaciones activas: %s", len(users)
            )

            notifications_sent = 0
            notifications_skipped = 0

            for user in users:
                if not user.notification_days:
                    logger.debug(
                        "[SCHEDULER V3] Usuario %s sin días configurados", user.username
                    )
                    continue

                selected_days = [day.strip() for day in user.notification_days.split(",")]
                if today_letter not in selected_days:
                    logger.debug(
                        "[SCHEDULER V3] Usuario %s sin hoy en días seleccionados %s",
                        user.username,
                        selected_days,
                    )
                    continue

                logger.debug(
                    "[SCHEDULER V3] Usuario %s procesando notificaciones", user.username
                )

                # Bloquear registro del usuario
                locked_user = (
                    db.session.query(User).filter_by(id=user.id).with_for_update().first()
                )

                # Entrada
                if locked_user.notification_time_entry:
                    entry_time = locked_user.notification_time_entry
                    diff_minutes = (
                        datetime.combine(datetime.today(), current_time)
                        - datetime.combine(datetime.today(), entry_time)
                    ).total_seconds() / 60

                    logger.debug(
                        "[SCHEDULER V3] Entrada %s diferencia %.1f min",
                        entry_time.strftime("%H:%M"),
                        diff_minutes,
                    )

                    if -2 <= diff_minutes <= 5:
                        already_sent = False
                        if locked_user.last_entry_notification_sent:
                            last_sent_date = locked_user.last_entry_notification_sent.date()
                            already_sent = last_sent_date == datetime.today().date()

                            if already_sent:
                                elapsed = (
                                    datetime.now()
                                    - locked_user.last_entry_notification_sent
                                )
                                mins = int(elapsed.total_seconds() / 60)
                                if elapsed.total_seconds() < 3600:
                                    logger.debug(
                                        "[SCHEDULER V3] Notificación ENTRADA ya enviada a %s hace %s minutos",
                                        locked_user.username,
                                        mins,
                                    )
                                else:
                                    logger.debug(
                                        "[SCHEDULER V3] Notificación ENTRADA ya enviada hoy a %s",
                                        locked_user.username,
                                    )

                        if already_sent:
                            notifications_skipped += 1
                        else:
                            logger.info(
                                "[SCHEDULER V3] Enviando email de ENTRADA a %s",
                                locked_user.username,
                            )
                            if send_notification_email_v3(mail, locked_user, "entry"):
                                notifications_sent += 1
                            else:
                                logger.error(
                                    "[SCHEDULER V3] Fallo al enviar email de ENTRADA a %s",
                                    locked_user.username,
                                )
                    else:
                        logger.debug(
                            "[SCHEDULER V3] Fuera de ventana de tiempo para ENTRADA"
                        )

                # Refrescar para salida
                locked_user = (
                    db.session.query(User).filter_by(id=user.id).with_for_update().first()
                )

                if locked_user.notification_time_exit:
                    exit_time = locked_user.notification_time_exit
                    diff_minutes = (
                        datetime.combine(datetime.today(), current_time)
                        - datetime.combine(datetime.today(), exit_time)
                    ).total_seconds() / 60

                    logger.debug(
                        "[SCHEDULER V3] Salida %s diferencia %.1f min",
                        exit_time.strftime("%H:%M"),
                        diff_minutes,
                    )

                    if -2 <= diff_minutes <= 5:
                        already_sent = False
                        if locked_user.last_exit_notification_sent:
                            last_sent_date = locked_user.last_exit_notification_sent.date()
                            already_sent = last_sent_date == datetime.today().date()

                            if already_sent:
                                elapsed = (
                                    datetime.now()
                                    - locked_user.last_exit_notification_sent
                                )
                                mins = int(elapsed.total_seconds() / 60)
                                if elapsed.total_seconds() < 3600:
                                    logger.debug(
                                        "[SCHEDULER V3] Notificación SALIDA ya enviada a %s hace %s minutos",
                                        locked_user.username,
                                        mins,
                                    )
                                else:
                                    logger.debug(
                                        "[SCHEDULER V3] Notificación SALIDA ya enviada hoy a %s",
                                        locked_user.username,
                                    )

                        if already_sent:
                            notifications_skipped += 1
                        else:
                            logger.info(
                                "[SCHEDULER V3] Enviando email de SALIDA a %s",
                                locked_user.username,
                            )
                            if send_notification_email_v3(mail, locked_user, "exit"):
                                notifications_sent += 1
                            else:
                                logger.error(
                                    "[SCHEDULER V3] Fallo al enviar email de SALIDA a %s",
                                    locked_user.username,
                                )
                    else:
                        logger.debug(
                            "[SCHEDULER V3] Fuera de ventana de tiempo para SALIDA"
                        )

                db.session.commit()

            logger.info(
                "[SCHEDULER V3] Revisión completada: %s enviados, %s omitidos",
                notifications_sent,
                notifications_skipped,
            )

        finally:
            try:
                db.session.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": LOCK_ID}
                )
                logger.debug("[SCHEDULER V3] Lock liberado")
            except Exception as e:  # noqa: BLE001
                logger.warning("[SCHEDULER V3] Error al liberar lock: %s", e)

