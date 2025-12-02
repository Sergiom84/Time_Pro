"""
Servicio de cálculo y gestión de horas extras.
"""
from datetime import datetime, date, timedelta
from models.models import User, TimeRecord, OvertimeEntry
from models.database import db
from sqlalchemy import func
from utils.logging_utils import get_logger

logger = get_logger(__name__)

TOLERANCE_SECONDS = 3600  # ±1 hora


def get_week_bounds(target_date):
    """
    Calcula el lunes y domingo de la semana que contiene target_date.

    Args:
        target_date: date object

    Returns:
        tuple: (week_start, week_end) como objetos date (lunes y domingo)
    """
    # Python considera lunes=0, domingo=6
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    weekday = target_date.weekday()
    week_start = target_date - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def calculate_weekly_worked_seconds(user_id, week_start, week_end):
    """
    Suma todos los segundos trabajados por user_id entre week_start y week_end.
    Solo cuenta registros cerrados (check_in y check_out no nulos).
    NO resta pausas (según requisitos del usuario).

    Args:
        user_id: ID del usuario
        week_start: date object (lunes)
        week_end: date object (domingo)

    Returns:
        int: Total de segundos trabajados en la semana
    """
    records = (
        TimeRecord.query
        .filter(
            TimeRecord.user_id == user_id,
            TimeRecord.date >= week_start,
            TimeRecord.date <= week_end,
            TimeRecord.check_in.isnot(None),
            TimeRecord.check_out.isnot(None)
        )
        .all()
    )

    total_seconds = 0
    for record in records:
        delta = record.check_out - record.check_in
        total_seconds += int(delta.total_seconds())

    return total_seconds


def generate_overtime_entries_for_week(client_id, target_date):
    """
    Genera/actualiza registros de overtime_entry para todos los usuarios activos
    del cliente, para la semana que contiene target_date.

    Solo crea registros si el delta excede la tolerancia de ±1 hora.
    Si ya existe un registro Pendiente, lo actualiza con los nuevos valores.
    Si existe pero está en otro estado (Aprobado/Ajustado), lo deja intacto.

    Args:
        client_id: ID del cliente
        target_date: date object de la semana a procesar

    Returns:
        tuple: (created_count, updated_count, skipped_count)
    """
    week_start, week_end = get_week_bounds(target_date)

    # Obtener usuarios activos del cliente
    users = User.query.filter_by(client_id=client_id, is_active=True).all()

    created = 0
    updated = 0
    skipped = 0

    for user in users:
        if user.weekly_hours == 0 or user.weekly_hours is None:
            skipped += 1
            continue

        # Calcular tiempo trabajado
        worked_secs = calculate_weekly_worked_seconds(user.id, week_start, week_end)
        contract_secs = user.weekly_hours * 3600
        delta_secs = worked_secs - contract_secs

        # Solo crear registro si excede tolerancia
        if abs(delta_secs) <= TOLERANCE_SECONDS:
            skipped += 1
            continue

        # Buscar si ya existe
        existing = OvertimeEntry.query.filter_by(
            client_id=client_id,
            user_id=user.id,
            week_start=week_start
        ).first()

        if existing:
            # Actualizar solo si está pendiente
            if existing.status == "Pendiente":
                existing.total_worked_seconds = worked_secs
                existing.contract_seconds = contract_secs
                existing.overtime_seconds = delta_secs
                existing.updated_at = datetime.utcnow()
                updated += 1
            else:
                # Ya fue procesado (Aprobado/Ajustado/Rechazado), no tocar
                skipped += 1
        else:
            # Crear nuevo
            entry = OvertimeEntry(
                client_id=client_id,
                user_id=user.id,
                week_start=week_start,
                week_end=week_end,
                total_worked_seconds=worked_secs,
                contract_seconds=contract_secs,
                overtime_seconds=delta_secs,
                status="Pendiente"
            )
            db.session.add(entry)
            created += 1

    db.session.commit()
    logger.info(f"Overtime generation for client {client_id}, week {week_start}: created={created}, updated={updated}, skipped={skipped}")

    return created, updated, skipped


def adjust_last_timerecord_auto(user_id, week_start, week_end, target_seconds):
    """
    Ajusta automáticamente el último TimeRecord de la semana para cuadrar
    el total semanal con target_seconds (generalmente contract_seconds).

    Modifica el check_out del último registro cerrado de la semana y
    añade una nota de auditoría en admin_notes.

    Args:
        user_id: ID del usuario
        week_start: date object (lunes)
        week_end: date object (domingo)
        target_seconds: Segundos objetivo (usualmente contract_seconds del empleado)

    Returns:
        bool: True si se ajustó correctamente, False si no fue posible
    """
    # Buscar último registro de la semana (cerrado)
    last_record = (
        TimeRecord.query
        .filter(
            TimeRecord.user_id == user_id,
            TimeRecord.date >= week_start,
            TimeRecord.date <= week_end,
            TimeRecord.check_in.isnot(None),
            TimeRecord.check_out.isnot(None)
        )
        .order_by(TimeRecord.date.desc(), TimeRecord.check_out.desc())
        .first()
    )

    if not last_record:
        logger.warning(f"No closed records found for user {user_id} in week {week_start}")
        return False

    # Calcular total sin el último registro
    other_records = (
        TimeRecord.query
        .filter(
            TimeRecord.user_id == user_id,
            TimeRecord.date >= week_start,
            TimeRecord.date <= week_end,
            TimeRecord.check_in.isnot(None),
            TimeRecord.check_out.isnot(None),
            TimeRecord.id != last_record.id
        )
        .all()
    )

    total_other = sum(
        int((r.check_out - r.check_in).total_seconds())
        for r in other_records
    )

    # Calcular cuánto debe durar el último registro
    needed_last = target_seconds - total_other

    if needed_last < 0:
        logger.warning(f"Cannot adjust: needed_last={needed_last} < 0 for user {user_id}")
        return False

    # Ajustar check_out del último registro
    new_checkout = last_record.check_in + timedelta(seconds=needed_last)

    # Guardar admin_notes indicando el ajuste
    old_checkout = last_record.check_out
    last_record.check_out = new_checkout

    # Añadir nota de auditoría
    adjustment_note = (
        f"[Ajuste automático horas extras {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}] "
        f"Checkout modificado de {old_checkout.strftime('%H:%M')} a {new_checkout.strftime('%H:%M')} "
        f"para cuadrar semana {week_start.strftime('%d/%m/%Y')}"
    )

    if last_record.admin_notes:
        last_record.admin_notes += f"\n{adjustment_note}"
    else:
        last_record.admin_notes = adjustment_note

    last_record.updated_at = datetime.utcnow()

    db.session.commit()
    logger.info(f"Adjusted TimeRecord {last_record.id} for user {user_id}: new_checkout={new_checkout}")

    return True
