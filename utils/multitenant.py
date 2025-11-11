"""
Utilidades para sistema multi-tenant (multi-cliente)
"""
from flask import session, g, request, redirect, url_for, abort
from functools import wraps
from models.models import Client, User
import os


def get_current_client():
    """
    Obtiene el cliente actual desde la sesión.
    Retorna el objeto Client o None.
    """
    if 'client_id' not in session:
        return None

    if not hasattr(g, 'current_client'):
        g.current_client = Client.query.get(session['client_id'])

    return g.current_client


def get_current_client_id():
    """
    Obtiene el ID del cliente actual desde la sesión.
    Retorna el ID o None.
    """
    return session.get('client_id')


def set_current_client(client_id):
    """
    Establece el cliente actual en la sesión.
    """
    session['client_id'] = client_id


def client_required(f):
    """
    Decorador que requiere que haya un cliente en la sesión.
    Si no hay cliente, redirige al login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'client_id' not in session:
            return redirect(url_for('auth_bp.login'))

        client = get_current_client()
        if not client or not client.is_active:
            session.clear()
            return redirect(url_for('auth_bp.login'))

        return f(*args, **kwargs)
    return decorated_function


def get_client_plan():
    """
    Obtiene el plan del cliente actual (lite o pro).
    Retorna 'pro' por defecto si no hay cliente.
    """
    client = get_current_client()
    if client:
        return client.plan

    # Fallback a la variable de entorno APP_PLAN
    return os.getenv('APP_PLAN', 'pro').lower()


def client_has_feature(feature_name):
    """
    Verifica si el cliente actual tiene acceso a una característica.

    Args:
        feature_name: Nombre de la característica (ej: 'email_notifications', 'multi_center')

    Returns:
        Boolean indicando si el cliente tiene acceso a la característica
    """
    plan = get_client_plan()

    # Características por plan
    PLAN_FEATURES = {
        'lite': {
            'basic_reports': True,
            'advanced_reports': False,
            'multi_center': False,
            'export_excel': True,
            'calendar_view': True,
            'leave_requests': True,
            'work_pauses': True,
            'email_notifications': False,
        },
        'pro': {
            'basic_reports': True,
            'advanced_reports': True,
            'multi_center': True,
            'export_excel': True,
            'calendar_view': True,
            'leave_requests': True,
            'work_pauses': True,
            'email_notifications': True,
        }
    }

    return PLAN_FEATURES.get(plan, PLAN_FEATURES['pro']).get(feature_name, False)


def get_client_config():
    """
    Obtiene la configuración completa del cliente actual.
    Similar a plan_config.py pero específico para el cliente.
    """
    client = get_current_client()
    plan = get_client_plan()

    is_lite = plan == 'lite'
    is_pro = plan == 'pro'

    config = {
        'plan': plan,
        'is_lite': is_lite,
        'is_pro': is_pro,
        'client_name': client.name if client else 'Time Pro',
        'client_slug': client.slug if client else 'timepro',
        'logo_url': client.logo_url if client else None,
        'primary_color': client.primary_color if client else '#0ea5e9',
        'secondary_color': client.secondary_color if client else '#06b6d4',
    }

    # Configuración por plan
    if is_lite:
        config.update({
            'max_employees': 5,
            'max_centers': 1,
            'show_center_selector': False,
            'center_label': 'Empresa',
            'center_label_plural': 'Empresas',
            'features': {
                'basic_reports': True,
                'advanced_reports': False,
                'multi_center': False,
                'export_excel': True,
                'calendar_view': True,
                'leave_requests': True,
                'work_pauses': True,
                'email_notifications': False,
            },
            'messages': {
                'employee_limit_reached': 'Has alcanzado el limite de 5 empleados de la version Lite.',
                'upgrade_prompt': 'Actualiza a la version Pro para anadir empleados ilimitados.'
            },
        })
    else:  # pro
        config.update({
            'max_employees': None,
            'max_centers': None,
            'show_center_selector': True,
            'center_label': 'Centro',
            'center_label_plural': 'Centros',
            'features': {
                'basic_reports': True,
                'advanced_reports': True,
                'multi_center': True,
                'export_excel': True,
                'calendar_view': True,
                'leave_requests': True,
                'work_pauses': True,
                'email_notifications': True,
            },
            'messages': {
                'employee_limit_reached': None,
                'upgrade_prompt': None
            },
        })

    return config


def inject_client_context():
    """
    Función para inyectar el contexto del cliente en los templates.
    Debe ser llamada desde un context_processor de Flask.
    """
    client = get_current_client()
    config = get_client_config() if client else {}

    return {
        'current_client': client,
        'client_config': config,
    }


def setup_multitenant_filters(app, db):
    """
    Configura filtros automáticos para aislar datos por client_id.

    Este sistema intercepta queries de SQLAlchemy y automáticamente
    agrega filtros WHERE client_id = X para modelos que tienen client_id.
    """
    from sqlalchemy import event, inspect
    from sqlalchemy.orm import Query

    # Modelos que tienen client_id y deben ser filtrados automáticamente
    TENANT_MODELS = ['User', 'TimeRecord', 'EmployeeStatus', 'WorkPause', 'LeaveRequest', 'SystemConfig']

    @event.listens_for(Query, "before_compile", retval=True)
    def before_compile(query):
        """
        Intercepta queries antes de compilarlas para agregar filtro de client_id.
        Solo aplica si hay un client_id en la sesión.
        """
        # Solo filtrar si hay un cliente en la sesión
        try:
            client_id = get_current_client_id()
            if not client_id:
                return query
        except RuntimeError:
            # No hay contexto de petición (ej: scripts, shell)
            # No aplicar filtro
            return query

        # Verificar si ya tiene un filtro de client_id
        # (para evitar duplicados)
        if hasattr(query, '_tenant_filtered'):
            return query

        # Iterar sobre las entidades en el query
        for ent in query.column_descriptions:
            entity = ent['entity']
            if entity is None:
                continue

            # Verificar si el modelo tiene client_id
            model_name = entity.__name__ if hasattr(entity, '__name__') else None
            if model_name in TENANT_MODELS:
                # Verificar que la columna client_id existe
                if hasattr(entity, 'client_id'):
                    # Agregar filtro automático
                    query = query.filter(entity.client_id == client_id)
                    query._tenant_filtered = True

        return query

    app.logger.info("Multi-tenant automatic filtering configured")
