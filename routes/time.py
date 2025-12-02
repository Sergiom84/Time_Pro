from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, jsonify, current_app
)
from sqlalchemy import desc, text, and_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date, timedelta
import calendar

from models.models import TimeRecord, User, EmployeeStatus, WorkPause, LeaveRequest
from models.database import db
from utils.file_utils import upload_file_to_supabase, validate_file
from utils.xss_utils import sanitize_text
from utils.helpers import format_timedelta
from utils.auth_decorators import client_required
from utils.query_helpers import time_records_query, employee_status_query, work_pauses_query, leave_requests_query
from utils.logging_utils import get_logger
from utils.db_helpers import db_transaction

time_bp = Blueprint("time", __name__)


# ------------------------------------------------------------------
#  FICHAR ENTRADA
# ------------------------------------------------------------------
@time_bp.route("/check_in", methods=["POST"])
@client_required
@db_transaction(flash_error=True)
def check_in(client_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]

    # BUSCA REGISTRO ABIERTO (de cualquier fecha)
    existing_open = time_records_query(
        user_id=user_id,
        include_open_only=True
    ).order_by(desc(TimeRecord.id)).first()

    if existing_open:
        # Si es de un día anterior, cerrarlo automáticamente
        if existing_open.date < date.today():
            from datetime import time as dt_time
            from models.models import WorkPause

            # Cerrar a las 23:59:59 de su fecha
            auto_close_time = datetime.combine(
                existing_open.date,
                dt_time(23, 59, 59)
            )
            existing_open.check_out = auto_close_time
            existing_open.notes = (existing_open.notes or "") + (" - " if existing_open.notes else "") + "Cerrado automáticamente al fichar nuevo día"

            # Cerrar pausas activas del registro antiguo
            WorkPause.query.filter(
                WorkPause.time_record_id == existing_open.id,
                WorkPause.pause_end.is_(None)
            ).update({
                WorkPause.pause_end: auto_close_time,
                WorkPause.notes: db.func.concat(
                    db.func.coalesce(WorkPause.notes, ""),
                    " - Cerrado automáticamente"
                )
            }, synchronize_session=False)

            db.session.commit()
            flash(f"Se cerró automáticamente tu fichaje del {existing_open.date.strftime('%d-%m-%Y')}.", "info")
            # Continuar con el nuevo fichaje (no return aquí)
        else:
            # Es del mismo día, no permitir otro fichaje
            flash(f"Tienes un fichaje abierto desde {existing_open.check_in.strftime('%d-%m-%Y %H:%M:%S')}. Debes cerrarlo antes de fichar entrada.", "warning")
            return redirect(url_for("time.dashboard_employee"))

    try:
        # 1) ¿Tiene hoy un estado NO trabajable?
        today_status = employee_status_query(
            user_id=user_id,
            date=date.today()
        ).first()

        if today_status and today_status.status in ("Vacaciones", "Baja", "Ausente"):
            flash(
                f"No puedes fichar — tu estado de hoy es «{today_status.status}».",
                "danger"
            )
            return redirect(url_for("time.dashboard_employee"))

        # 2) Bloqueo en Postgres (por si lo usas)
        bind = db.session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            db.session.execute(
                text("LOCK TABLE public.time_record IN SHARE ROW EXCLUSIVE MODE")
            )

        # 3) ¿Ya hay un fichaje abierto HOY? (los del día anterior ya se cerraron arriba)
        existing_open_today = time_records_query(
            user_id=user_id,
            include_open_only=True
        ).filter_by(date=date.today()).order_by(desc(TimeRecord.id)).first()

        if existing_open_today:
            flash(
                f"Ya tienes un registro abierto desde "
                f"{existing_open_today.check_in.strftime('%d-%m-%Y %H:%M:%S')}.",
                "warning"
            )
        else:
            now = datetime.now()

            # --- crear TimeRecord ---
            new_rec = TimeRecord(
                client_id=client_id,
                user_id=user_id,
                check_in=now,
                date=now.date()
            )
            db.session.add(new_rec)
            db.session.flush()  # Genera el ID del registro

            # --- SELLAR EL FICHAJE (Ley de Fichajes) ---
            from services.timestamp_service import TimestampService
            from models.models import TimeRecordSignature

            try:
                content_hash, signature, timestamp_utc, terminal_id = TimestampService.seal_record(
                    time_record=new_rec,
                    action="check_in",
                    request=request
                )

                # Crear registro de firma
                sig = TimeRecordSignature(
                    time_record_id=new_rec.id,
                    client_id=client_id,
                    timestamp_utc=timestamp_utc,
                    action="check_in",
                    terminal_id=terminal_id,
                    user_agent=request.headers.get("User-Agent"),
                    ip_address=request.remote_addr,
                    content_hash=content_hash,
                    signature=signature,
                    key_version=1
                )
                db.session.add(sig)
            except Exception as e:
                current_app.logger.error(f"Error al sellar check-in: {str(e)}")
                # Continuar aunque falle el sellado (no bloquear al usuario)

            # --- si no existe EmployeeStatus hoy, crearlo como Trabajado ---
            if not today_status:
                db.session.add(EmployeeStatus(
                    client_id=client_id,
                    user_id=user_id,
                    date=now.date(),
                    status="Trabajado",
                    notes="Registro automático de fichaje"
                ))

            db.session.commit()
            flash("Entrada registrada correctamente.", "success")

    except Exception:
        # Re-lanzar excepciones que no sean SQLAlchemyError para que el decorador las maneje
        raise

    return redirect(url_for("time.dashboard_employee"))


# ------------------------------------------------------------------
#  FICHAR SALIDA
# ------------------------------------------------------------------
@time_bp.route("/check_out", methods=["POST"])
@client_required
@db_transaction(flash_error=True)
def check_out(client_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]

    try:
        bind = db.session.get_bind()
        if bind and bind.dialect.name == "postgresql":
            db.session.execute(
                text("LOCK TABLE public.time_record IN SHARE ROW EXCLUSIVE MODE")
            )

        open_record = time_records_query(
            user_id=user_id,
            include_open_only=True
        ).order_by(desc(TimeRecord.id)).first()

        if open_record:
            now = datetime.now()
            open_record.check_out = now
            open_record.notes = sanitize_text(request.form.get("notes", ""))

            # --- SELLAR EL FICHAJE (Ley de Fichajes) ---
            from services.timestamp_service import TimestampService
            from models.models import TimeRecordSignature

            try:
                content_hash, signature, timestamp_utc, terminal_id = TimestampService.seal_record(
                    time_record=open_record,
                    action="check_out",
                    request=request
                )

                # Crear registro de firma
                sig = TimeRecordSignature(
                    time_record_id=open_record.id,
                    client_id=client_id,
                    timestamp_utc=timestamp_utc,
                    action="check_out",
                    terminal_id=terminal_id,
                    user_agent=request.headers.get("User-Agent"),
                    ip_address=request.remote_addr,
                    content_hash=content_hash,
                    signature=signature,
                    key_version=1
                )
                db.session.add(sig)
            except Exception as e:
                current_app.logger.error(f"Error al sellar check-out: {str(e)}")
                # Continuar aunque falle el sellado (no bloquear al usuario)

            db.session.commit()
            flash("Salida registrada correctamente.", "success")
        else:
            flash("No tienes ningún fichaje abierto.", "warning")

    except Exception:
        # Re-lanzar excepciones para que el decorador @db_transaction las maneje
        raise

    return redirect(url_for("time.dashboard_employee"))


# ------------------------------------------------------------------
#  DASHBOARD EMPLEADO
# ------------------------------------------------------------------
@time_bp.route("/dashboard")
def dashboard():
    return redirect(url_for("time.dashboard_employee"))


@time_bp.route("/employee/dashboard")
def dashboard_employee():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week   = start_week + timedelta(days=7)

    weekly_records = (
        time_records_query(user_id=user_id)
        .filter(
            TimeRecord.date >= start_week,
            TimeRecord.date < end_week,
            TimeRecord.check_in.isnot(None),
            TimeRecord.check_out.isnot(None)
        )
        .all()
    )

    worked_secs   = sum((r.check_out - r.check_in).total_seconds() for r in weekly_records)
    allowed_secs  = (user.weekly_hours or 0) * 3600
    remain_secs   = max(allowed_secs - worked_secs, 0)

    recent = time_records_query(user_id=user_id) \
        .order_by(desc(TimeRecord.date), desc(TimeRecord.check_in)) \
        .limit(3) \
        .all()

    recent_fmt = []
    for rec in recent:
        dur = rec.check_out - rec.check_in if rec.check_in and rec.check_out else None
        recent_fmt.append({
            "record": rec,
            "duration_formatted": format_timedelta(dur),
            "remaining": format_timedelta(timedelta(seconds=remain_secs)),
            "is_over": remain_secs == 0
        })

    today_record = time_records_query(user_id=user_id, include_open_only=True) \
        .filter_by(date=today) \
        .order_by(desc(TimeRecord.id)) \
        .first()

    # Obtener pausa activa SOLO del fichaje de hoy (si existe)
    active_pause = None
    if today_record:
        active_pause = (
            WorkPause.query
            .filter_by(
                time_record_id=today_record.id,  # Solo del fichaje actual
                pause_end=None
            )
            .order_by(desc(WorkPause.id))
            .first()
        )

    return render_template(
        "employee_dashboard.html",
        user=user,
        today_record=today_record,
        recent_records=recent_fmt,
        active_pause=active_pause,
        client_logo_url=user.client.logo_url if getattr(user, "client", None) else None
    )


# ------------------------------------------------------------------
#  HISTÓRICO INDIVIDUAL
# ------------------------------------------------------------------
@time_bp.route("/history")
def history():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]

    recs = time_records_query(user_id=user_id) \
        .order_by(desc(TimeRecord.id)) \
        .all()
    data = []
    for r in recs:
        dur = r.check_out - r.check_in if r.check_in and r.check_out else None
        data.append({"record": r, "duration_formatted": format_timedelta(dur)})

    return render_template("history.html", records=data)


# ------------------------------------------------------------------
#  CALENDARIO SIMPLE (vista antigua)
# ------------------------------------------------------------------
@time_bp.route("/calendar")
def calendar_view():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    year  = request.args.get("year",  default=date.today().year,  type=int)
    month = request.args.get("month", default=date.today().month, type=int)

    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(year, month)

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_days=month_days
    )


# ------------------------------------------------------------------
#  PREFERENCIAS DE NOTIFICACIONES POR CORREO
# ------------------------------------------------------------------
@time_bp.route("/notifications/preferences", methods=["GET"])
def get_notification_preferences():
    """Obtener las preferencias de notificación del usuario actual"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)

    return jsonify({
        "email_notifications": user.email_notifications,
        "notification_days": user.notification_days or "",
        "notification_time_entry": user.notification_time_entry.strftime("%H:%M") if user.notification_time_entry else "",
        "notification_time_exit": user.notification_time_exit.strftime("%H:%M") if user.notification_time_exit else "",
        "additional_notification_email": user.additional_notification_email or ""
    })


@time_bp.route("/notifications/preferences", methods=["POST"])
def save_notification_preferences():
    """Guardar las preferencias de notificación del usuario"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    try:
        user_id = session["user_id"]
        user = User.query.get_or_404(user_id)

        data = request.get_json()

        # Actualizar preferencias
        user.email_notifications = data.get("email_notifications", False)
        user.notification_days = data.get("notification_days", "")
        user.additional_notification_email = data.get("additional_notification_email", "")

        # Convertir horarios de string a time
        entry_time_str = data.get("notification_time_entry", "")
        exit_time_str = data.get("notification_time_exit", "")

        if entry_time_str:
            try:
                user.notification_time_entry = datetime.strptime(entry_time_str, "%H:%M").time()
            except ValueError:
                return jsonify({"error": "Formato de hora de entrada inválido"}), 400
        else:
            user.notification_time_entry = None

        if exit_time_str:
            try:
                user.notification_time_exit = datetime.strptime(exit_time_str, "%H:%M").time()
            except ValueError:
                return jsonify({"error": "Formato de hora de salida inválido"}), 400
        else:
            user.notification_time_exit = None

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Preferencias guardadas correctamente"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------
#  GESTIÓN DE PAUSAS/DESCANSOS
# ------------------------------------------------------------------
@time_bp.route("/time/pause/active", methods=["GET"])
def get_active_pause():
    """Obtener pausa activa del usuario"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]

    # Buscar pausa activa (sin pause_end)
    active_pause = WorkPause.query.filter_by(
        user_id=user_id,
        pause_end=None
    ).order_by(desc(WorkPause.id)).first()

    if active_pause:
        return jsonify({
            "active_pause": {
                "id": active_pause.id,
                "pause_type": active_pause.pause_type,
                "start_time": active_pause.pause_start.strftime("%H:%M:%S"),
                "start_timestamp": active_pause.pause_start.isoformat()
            }
        })
    else:
        return jsonify({"active_pause": None})


@time_bp.route("/time/pause/start", methods=["POST"])
@client_required
@db_transaction(flash_error=True)
def start_pause(client_id):
    """Iniciar una pausa/descanso (con soporte para adjuntar archivos)"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]

    # Soporte para JSON y FormData (con archivos)
    if request.is_json:
        data = request.get_json()
        file = None
    else:
        data = request.form.to_dict()
        file = request.files.get('attachment')

    try:
        # Verificar que el usuario tiene un fichaje abierto hoy
        today_record = time_records_query(
            user_id=user_id
        ).filter_by(
            date=date.today(),
            check_out=None
        ).order_by(desc(TimeRecord.id)).first()

        if not today_record:
            return jsonify({
                "success": False,
                "error": "No tienes un fichaje activo. Debes fichar entrada primero."
            })

        # Verificar que no haya una pausa activa
        active_pause = work_pauses_query(
            user_id=user_id,
            include_active_only=True
        ).first()

        if active_pause:
            return jsonify({
                "success": False,
                "error": "Ya tienes una pausa activa. Debes finalizarla antes de iniciar otra."
            })
        # Crear nueva pausa
        new_pause = WorkPause(
            client_id=client_id,
            user_id=user_id,
            time_record_id=today_record.id,
            pause_type=data.get("pause_type", "Descanso"),
            pause_start=datetime.now(),
            notes=sanitize_text(data.get("notes", ""))
        )

        # Si hay archivo adjunto, subirlo a Supabase Storage
        if file and file.filename:
            success, message, file_data = upload_file_to_supabase(
                file=file,
                user_id=user_id,
                folder="pausas"
            )

            if success:
                new_pause.attachment_url = file_data.get("url")
                new_pause.attachment_filename = file_data.get("filename")
                new_pause.attachment_type = file_data.get("mime_type")
                new_pause.attachment_size = file_data.get("size")
            else:
                return jsonify({
                    "success": False,
                    "error": f"Error al subir archivo: {message}"
                }), 400

        db.session.add(new_pause)
        db.session.commit()

        response_data = {
            "success": True,
            "message": "Pausa iniciada correctamente",
            "pause_id": new_pause.id
        }

        if new_pause.attachment_url:
            response_data["attachment"] = {
                "filename": new_pause.attachment_filename,
                "url": new_pause.attachment_url
            }

        return jsonify(response_data)

    except Exception as e:
        # Re-lanzar para que el decorador @db_transaction las maneje
        raise


@time_bp.route("/time/pause/end/<int:pause_id>", methods=["POST"])
@db_transaction(flash_error=True)
def end_pause(pause_id):
    """Finalizar una pausa/descanso"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]

    try:
        # Buscar la pausa
        pause = WorkPause.query.filter_by(
            id=pause_id,
            user_id=user_id,
            pause_end=None
        ).first()

        if not pause:
            return jsonify({
                "success": False,
                "error": "No se encontró la pausa activa"
            })

        # Finalizar la pausa
        pause.pause_end = datetime.now()
        db.session.commit()

        # Calcular duración
        duration = pause.pause_end - pause.pause_start
        duration_minutes = int(duration.total_seconds() / 60)

        return jsonify({
            "success": True,
            "message": f"Pausa finalizada. Duración: {duration_minutes} minutos"
        })

    except Exception as e:
        # Re-lanzar para que el decorador @db_transaction las maneje
        raise


# ------------------------------------------------------------------
#  GESTIÓN DE SOLICITUDES DE VACACIONES/BAJAS/AUSENCIAS
# ------------------------------------------------------------------
@time_bp.route("/time/requests/new", methods=["POST"])
@client_required
@db_transaction(flash_error=True)
def create_leave_request(client_id):
    """Crear nueva solicitud de vacaciones/baja/ausencia (con soporte para adjuntar archivos)"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]

    # Soporte para JSON y FormData (con archivos)
    if request.is_json:
        data = request.get_json()
        file = None
    else:
        data = request.form.to_dict()
        file = request.files.get('attachment')

    try:
        # Validar fechas
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()

        if start_date > end_date:
            return jsonify({
                "success": False,
                "error": "La fecha de inicio no puede ser posterior a la fecha de fin"
            })

        # Determinar el estado inicial según el tipo de solicitud
        request_type = data["request_type"]

        # Todas las solicitudes ahora requieren aprobación
        # Se unificó el flujo: todos los tipos usan "Pendiente" → "Aprobado"/"Rechazado"
        status = "Pendiente"
        approval_date = None
        # Crear nueva solicitud
        new_request = LeaveRequest(
            client_id=client_id,
            user_id=user_id,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            reason=sanitize_text(data.get("reason", "")),
            status=status,
            approval_date=approval_date
        )

        # Si hay archivo adjunto, subirlo a Supabase Storage
        if file and file.filename:
            logger = get_logger(__name__)
            logger.info(f"📎 Procesando archivo adjunto: {file.filename}")
            logger.debug(f"   Content-Type: {file.content_type}")
            logger.debug(f"   Tamaño aproximado: {file.content_length if hasattr(file, 'content_length') else 'desconocido'}")

            try:
                success, message, file_data = upload_file_to_supabase(
                    file=file,
                    user_id=user_id,
                    folder="solicitudes"
                )

                if success:
                    new_request.attachment_url = file_data.get("url")
                    new_request.attachment_filename = file_data.get("filename")
                    new_request.attachment_type = file_data.get("mime_type")
                    new_request.attachment_size = file_data.get("size")
                    logger = get_logger(__name__)
                    logger.info(f"File uploaded successfully: {file_data.get('url')}")
                else:
                    logger = get_logger(__name__)
                    logger.warning(f"Error uploading file: {message}")
                    return jsonify({
                        "success": False,
                        "error": message
                    }), 400

            except Exception as file_error:
                error_msg = str(file_error)
                logger = get_logger(__name__)
                logger.error(f"Exception processing file: {error_msg}")
                logger.debug(f"Exception type: {type(file_error).__name__}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), 400

        db.session.add(new_request)
        db.session.flush()  # Para obtener el ID

        db.session.commit()

        # Mensaje unificado: todas las solicitudes requieren aprobación
        message = "Solicitud enviada correctamente. Pendiente de aprobación del administrador"

        response_data = {
            "success": True,
            "message": message,
            "request_id": new_request.id,
            "status": status
        }

        if new_request.attachment_url:
            response_data["attachment"] = {
                "filename": new_request.attachment_filename,
                "url": new_request.attachment_url
            }

        return jsonify(response_data)

    except Exception as e:
        # Re-lanzar para que el decorador @db_transaction las maneje
        raise


@time_bp.route("/time/requests/my", methods=["GET"])
def get_my_requests():
    """Obtener solicitudes del usuario actual"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]

    try:
        requests = LeaveRequest.query.filter_by(
            user_id=user_id
        ).order_by(desc(LeaveRequest.created_at)).all()

        requests_data = []
        for req in requests:
            requests_data.append({
                "id": req.id,
                "request_type": req.request_type,
                "start_date": req.start_date.strftime("%Y-%m-%d"),
                "end_date": req.end_date.strftime("%Y-%m-%d"),
                "reason": req.reason,
                "status": req.status,
                "created_at": req.created_at.strftime("%Y-%m-%d %H:%M")
            })

        return jsonify({
            "success": True,
            "requests": requests_data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@time_bp.route("/time/requests/cancel/<int:request_id>", methods=["POST"])
def cancel_leave_request(request_id):
    """Cancelar una solicitud pendiente o enviada"""
    if "user_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    user_id = session["user_id"]

    try:
        # Buscar la solicitud (permitir cancelar si está Pendiente o Enviada)
        leave_request = LeaveRequest.query.filter(
            LeaveRequest.id == request_id,
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_(["Pendiente", "Enviado"])
        ).first()

        if not leave_request:
            return jsonify({
                "success": False,
                "error": "No se encontró la solicitud o ya no se puede cancelar (puede estar aprobada o rechazada)"
            })

        # Cancelar la solicitud
        leave_request.status = "Cancelado"
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Solicitud cancelada correctamente"
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ------------------------------------------------------------------
#  PROCESAMIENTO AUTOMÁTICO DE SOLICITUDES APROBADAS
# ------------------------------------------------------------------
def process_approved_requests():
    """Procesar solicitudes aprobadas y actualizar EmployeeStatus"""
    today = date.today()

    # Buscar solicitudes aprobadas que incluyan hoy
    approved_requests = LeaveRequest.query.filter(
        LeaveRequest.status == "Aprobado",
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).all()

    for req in approved_requests:
        # Mapeo de tipos de solicitud a estados de empleado
        # Mapeo de tipos de solicitud a estados de empleado
        status_map = {
            "Vacaciones": "Vacaciones",
            "Baja médica": "Baja",
            "Ausencia justificada": "Ausente",
            "Ausencia injustificada": "Ausente",
            "Permiso especial": "Vacaciones"
        }

        status = status_map.get(req.request_type, "Ausente")

        # Actualizar o crear EmployeeStatus para cada día del rango
        current_date = req.start_date
        while current_date <= req.end_date and current_date <= today:
            # Verificar si ya existe un status para ese día
            existing_status = EmployeeStatus.query.filter_by(
                user_id=req.user_id,
                date=current_date
            ).first()

            if existing_status:
                # Actualizar si es diferente
                if existing_status.status != status:
                    existing_status.status = status
                    existing_status.request_type = req.request_type
                    existing_status.notes = f"Actualizado por solicitud aprobada: {req.request_type}"
            else:
                # Crear nuevo status
                new_status = EmployeeStatus(
                    client_id=req.client_id,  # Multi-tenant: obtener de la solicitud
                    user_id=req.user_id,
                    date=current_date,
                    status=status,
                    request_type=req.request_type,
                    notes=f"Generado por solicitud aprobada: {req.request_type}"
                )
                db.session.add(new_status)

            current_date += timedelta(days=1)

    db.session.commit()

