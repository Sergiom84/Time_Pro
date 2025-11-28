"""
Sistema de configuracion multi-plan para Time Pro
Permite alternar entre version Lite y Pro mediante variable de entorno
"""
import os

# Determinar el plan activo desde variable de entorno
# Por defecto: 'pro' (si no esta definida la variable)
PLAN = os.getenv('APP_PLAN', 'pro').lower()

# Validar que el plan sea valido
if PLAN not in ['lite', 'pro']:
    print(f"ADVERTENCIA: Plan '{PLAN}' no valido. Usando 'pro' por defecto.")
    PLAN = 'pro'

# Configuracion especifica por plan
PLAN_CONFIG = {
    'lite': {
        # Limites de usuarios
        'max_employees': 10,
        'max_centers': 1,

        # UI/UX
        'show_center_selector': False,
        'center_label': 'Empresa',
        'center_label_plural': 'Empresas',

        # Caracteristicas disponibles
        'features': {
            'basic_reports': True,
            'advanced_reports': False,
            'multi_center': False,
            'export_excel': True,
            'calendar_view': True,
            'leave_requests': True,
            'work_pauses': True,
            'email_notifications': True,  # Habilitado en Lite
        },

        # Mensajes personalizados
        'messages': {
            'employee_limit_reached': 'Has alcanzado el limite de 10 empleados de la version Lite.',
            'upgrade_prompt': 'Actualiza a la version Pro para anadir empleados ilimitados.',
        }
    },

    'pro': {
        # Limites de usuarios
        'max_employees': None,  # Ilimitado
        'max_centers': None,    # Ilimitado

        # UI/UX
        'show_center_selector': True,
        'center_label': 'Centro',
        'center_label_plural': 'Centros',

        # Caracteristicas disponibles
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

        # Mensajes personalizados
        'messages': {
            'employee_limit_reached': None,  # No hay limite
            'upgrade_prompt': None,
        }
    }
}

def get_config():
    """Obtiene la configuracion del plan activo"""
    return PLAN_CONFIG[PLAN]

def get_plan():
    """Obtiene el nombre del plan activo"""
    return PLAN

def is_lite():
    """Verifica si el plan activo es Lite"""
    return PLAN == 'lite'

def is_pro():
    """Verifica si el plan activo es Pro"""
    return PLAN == 'pro'

def has_feature(feature_name):
    """Verifica si una caracteristica esta disponible en el plan actual"""
    return get_config()['features'].get(feature_name, False)

# Constantes de acceso rapido (compatibilidad con codigo existente)
MAX_EMPLOYEES = get_config()['max_employees']
MAX_CENTERS = get_config()['max_centers']
SHOW_CENTER_SELECTOR = get_config()['show_center_selector']
CENTER_LABEL = get_config()['center_label']
CENTER_LABEL_PLURAL = get_config()['center_label_plural']

# Logging del plan activo al importar (no bloquear si no hay stdout)
try:
    print(f"✓ Time Pro iniciado con plan: {PLAN.upper()}")
    print(f"  - Limite de empleados: {MAX_EMPLOYEES or 'Ilimitado'}")
    print(f"  - Multiples centros: {'Si' if SHOW_CENTER_SELECTOR else 'No'}")
except Exception:
    pass

