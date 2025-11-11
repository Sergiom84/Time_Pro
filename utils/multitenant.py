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
            'center_label_plural': 'Empresa',
            'features': {
                'basic_reports': True,
                'advanced_reports': False,
                'multi_center': False,
                'export_excel': True,
                'calendar_view': True,
                'leave_requests': True,
                'work_pauses': True,
                'email_notifications': False,
            }
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
            }
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
