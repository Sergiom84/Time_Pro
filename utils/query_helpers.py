"""
Helpers para construir queries multi-tenant de forma centralizada.

IMPORTANTE: TenantAwareQuery ya filtra automáticamente por client_id
según la sesión actual. Estos helpers solo parametrizan filtros adicionales.

Solo funcionan dentro de peticiones Flask (con app context).
"""

from models.models import TimeRecord, EmployeeStatus, WorkPause, LeaveRequest


def time_records_query(user_id=None, include_open_only=False):
    """
    Query base para TimeRecord con filtrado adicional.
    TenantAwareQuery aplica client_id automáticamente según sesión.

    Args:
        user_id: Filtrar por usuario específico (None = todos)
        include_open_only: Si True, solo registros sin check_out (abiertos)

    Returns:
        Query filtrada y lista para usar (.first(), .all(), etc.)

    Ejemplo:
        # Obtener registro abierto del usuario actual
        open_record = time_records_query(
            user_id=user_id,
            include_open_only=True
        ).order_by(desc(TimeRecord.id)).first()

        # Obtener todos los registros de hoy para un usuario
        today_records = time_records_query(
            user_id=user_id
        ).filter_by(date=date.today()).all()
    """
    query = TimeRecord.query  # TenantAwareQuery aplica client_id automáticamente

    if user_id:
        query = query.filter_by(user_id=user_id)

    if include_open_only:
        query = query.filter_by(check_out=None)

    return query


def employee_status_query(user_id=None, date=None):
    """
    Query base para EmployeeStatus con filtrado adicional.
    TenantAwareQuery aplica client_id automáticamente según sesión.

    Args:
        user_id: Filtrar por usuario específico (None = todos)
        date: Filtrar por fecha específica (None = todas)

    Returns:
        Query filtrada y lista para usar (.first(), .all(), etc.)

    Ejemplo:
        # Obtener estado de un usuario para hoy
        today_status = employee_status_query(
            user_id=user_id,
            date=date.today()
        ).first()

        # Obtener todos los estados de un usuario
        all_statuses = employee_status_query(
            user_id=user_id
        ).all()
    """
    query = EmployeeStatus.query  # TenantAwareQuery aplica client_id

    if user_id:
        query = query.filter_by(user_id=user_id)

    if date:
        query = query.filter_by(date=date)

    return query


def work_pauses_query(user_id=None, include_active_only=False):
    """
    Query base para WorkPause con filtrado adicional.
    TenantAwareQuery aplica client_id automáticamente según sesión.

    Args:
        user_id: Filtrar por usuario específico (None = todos)
        include_active_only: Si True, solo pausas sin pause_end (activas)

    Returns:
        Query filtrada y lista para usar (.first(), .all(), etc.)

    Ejemplo:
        # Obtener pausa activa del usuario
        active_pause = work_pauses_query(
            user_id=user_id,
            include_active_only=True
        ).order_by(desc(WorkPause.id)).first()
    """
    query = WorkPause.query  # TenantAwareQuery aplica client_id

    if user_id:
        query = query.filter_by(user_id=user_id)

    if include_active_only:
        query = query.filter_by(pause_end=None)

    return query


def leave_requests_query(user_id=None, status=None):
    """
    Query base para LeaveRequest con filtrado adicional.
    TenantAwareQuery aplica client_id automáticamente según sesión.

    Args:
        user_id: Filtrar por usuario específico (None = todos)
        status: Filtrar por estado específico (None = todos)
                Valores válidos: "Pendiente", "Aprobado", "Rechazado", "Cancelado"

    Returns:
        Query filtrada y lista para usar (.first(), .all(), etc.)

    Ejemplo:
        # Obtener solicitudes pendientes de un usuario
        pending_requests = leave_requests_query(
            user_id=user_id,
            status="Pendiente"
        ).all()

        # Obtener todas las solicitudes aprobadas
        approved = leave_requests_query(
            status="Aprobado"
        ).all()
    """
    query = LeaveRequest.query  # TenantAwareQuery aplica client_id

    if user_id:
        query = query.filter_by(user_id=user_id)

    if status:
        query = query.filter_by(status=status)

    return query
