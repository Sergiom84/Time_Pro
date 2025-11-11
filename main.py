import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix para forzar conexiones IPv4 con Supabase PostgreSQL
# IMPORTANTE: Debe estar ANTES de cualquier import de Flask/SQLAlchemy/psycopg2
# Soluciona problemas de timeout con IPv6 en Windows/WSL
import socket
_original_getaddrinfo = socket.getaddrinfo
def _force_ipv4_getaddrinfo(*args, **kwargs):
    """
    Forzar conexiones PostgreSQL a usar IPv4 en lugar de IPv6.
    Solo se aplica a hosts de Supabase pooler, no afecta otras conexiones.
    """
    host = args[0] if args else kwargs.get('host', '')

    # Solo aplicar fix a hosts de PostgreSQL/pooler de Supabase
    if 'pooler.supabase.com' in str(host) or 'supabase.co' in str(host) and 'db.' in str(host):
        kwargs['family'] = socket.AF_INET

    return _original_getaddrinfo(*args, **kwargs)
socket.getaddrinfo = _force_ipv4_getaddrinfo

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_mail import Mail
from models.database import db
from flask_migrate import Migrate, upgrade as migrate_upgrade
from routes.auth import auth_bp
from routes.time import time_bp
from routes.admin import admin_bp
from routes.export import export_bp
import plan_config  # Sistema de configuración multi-plan
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    import atexit
    SCHEDULER_AVAILABLE = True
except ImportError as e:
    print(f"APScheduler not available: {e}", file=sys.stderr)
    SCHEDULER_AVAILABLE = False

# Crear instancia de la app Flask
app = Flask(
    __name__,
    static_folder='static',
    template_folder='src/templates'
)

# Configuración general
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configuración de límite de tamaño de petición HTTP
# Permitir archivos de hasta 16MB en las peticiones HTTP
# (el límite real de validación en el código es 5MB, pero necesitamos
# este margen para que la petición llegue al código de validación)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Configuración de la base de datos
# TODAS las credenciales deben estar en el archivo .env
# NO se permiten credenciales hardcodeadas en el código

# Leer DATABASE_URL desde .env (obligatorio)
uri = os.getenv("DATABASE_URL")
if not uri:
    raise ValueError(
        "DATABASE_URL no está configurada. "
        "Por favor, configura DATABASE_URL en el archivo .env"
    )

# Normalizar si viniera como postgres://
uri = uri.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_DATABASE_URI'] = uri

def _mask_dsn(dsn: str) -> str:
    try:
        from urllib.parse import urlparse
        p = urlparse(dsn)
        if p.password:
            return dsn.replace(p.password, "****")
        return dsn
    except Exception:
        return dsn

print("Usando BD:", _mask_dsn(app.config['SQLALCHEMY_DATABASE_URI']), file=sys.stderr)

# Configure SQLAlchemy engine options based on environment
is_production = os.getenv('DYNO') or os.getenv('RENDER')
if is_production:
    # Production environment - standard pooling for sync workers
    # Configurado para usar Connection Pooler (puerto 6543)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "connect_args": {
            "connect_timeout": 10,
            "sslmode": "require",     # SSL requerido para Supabase
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    }
else:
    # Development environment - use minimal pooling (Supabase free tier)
    # Configurado para usar Connection Pooler (puerto 6543)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,       # Verificar conexión antes de usar
        "pool_recycle": 300,          # Reciclar conexiones cada 5 min
        "pool_size": 1,               # Solo 1 conexión (mínimo absoluto)
        "max_overflow": 2,            # 2 extras si es necesario
        "pool_timeout": 30,           # Timeout para obtener conexión del pool
        "connect_args": {
            "connect_timeout": 15,    # Timeout más largo para IPv6
            "sslmode": "require",     # SSL requerido para Supabase
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "options": "-c statement_timeout=30000",  # 30s statement timeout
        }
    }
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

# Inicializar extensiones
db.init_app(app)
mail = Mail(app)

# Inicializar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Log rápido del driver efectivo
try:
    with app.app_context():
        print("Driver:", db.engine.url.drivername, file=sys.stderr)
except Exception:
    pass
# Log de diagnóstico por request para confirmar motor/URL
@app.before_request
def _log_db_on_request():
    try:
        from flask import request
        print(f"[REQ] {request.method} {request.path} -> engine={db.engine.url.drivername} url={db.engine.url}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[REQ] engine-info error: {e}", file=sys.stderr, flush=True)

migrate = Migrate(app, db)

# Proper session cleanup
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Context processor para hacer disponible el usuario actual, saludo y configuración del plan
@app.context_processor
def inject_user():
    from flask import session
    from models.models import User, SystemConfig, Client
    from datetime import datetime
    from utils.multitenant import get_current_client, get_client_config

    user = None
    greeting = ""
    current_client = None
    client_config_dict = {}

    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            # Obtener solo el primer nombre
            first_name = user.full_name.split()[0] if user.full_name else user.username

            # Determinar saludo según la hora
            hour = datetime.now().hour
            if 6 <= hour < 12:
                greeting = f"Buenos días, {first_name}"
            elif 12 <= hour < 20:
                greeting = f"Buenas tardes, {first_name}"
            else:
                greeting = f"Buenas noches, {first_name}"

            # Obtener cliente actual (multi-tenant)
            current_client = get_current_client()
            client_config_dict = get_client_config()

    # Obtener el tema actual del usuario (si está autenticado) o el tema por defecto
    if user:
        current_theme = user.theme_preference
    else:
        current_theme = 'dark-turquoise'  # Tema por defecto para usuarios no autenticados

    # Inyectar configuración del plan en todos los templates
    # Si hay cliente, usar su configuración, sino usar la global
    if client_config_dict:
        plan_config_dict = {
            'plan': client_config_dict['plan'],
            'is_lite': client_config_dict['is_lite'],
            'is_pro': client_config_dict['is_pro'],
            'show_center_selector': client_config_dict['show_center_selector'],
            'center_label': client_config_dict['center_label'],
            'center_label_plural': client_config_dict['center_label_plural'],
            'max_employees': client_config_dict['max_employees'],
            'features': client_config_dict['features']
        }
    else:
        # Fallback a configuración global
        plan_config_dict = {
            'plan': plan_config.get_plan(),
            'is_lite': plan_config.is_lite(),
            'is_pro': plan_config.is_pro(),
            'show_center_selector': plan_config.SHOW_CENTER_SELECTOR,
            'center_label': plan_config.CENTER_LABEL,
            'center_label_plural': plan_config.CENTER_LABEL_PLURAL,
            'max_employees': plan_config.MAX_EMPLOYEES,
            'features': plan_config.get_config()['features']
        }

    return dict(
        current_user=user,
        greeting=greeting,
        current_theme=current_theme,
        plan_config=plan_config_dict,
        current_client=current_client,
        client_config=client_config_dict
    )

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(time_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(export_bp)

# Manejador de errores para archivos demasiado grandes
@app.errorhandler(413)
def request_entity_too_large(error):
    """Manejar error cuando el archivo excede MAX_CONTENT_LENGTH"""
    from flask import jsonify, request
    if request.path.startswith('/time/'):
        # Si es una petición AJAX, devolver JSON
        return jsonify({
            'success': False,
            'error': 'El archivo es demasiado grande. El tamaño máximo permitido es 16MB.'
        }), 413
    else:
        # Si es una petición normal, devolver HTML
        return render_template('error.html',
            error_message='El archivo es demasiado grande. El tamaño máximo permitido es 16MB.'), 413

# Ruta de inicio
@app.route('/')
def index():
    return render_template("welcome.html")

# WebSocket events para temas individuales (sin sincronización global)
@socketio.on('connect')
def handle_connect():
    """Manejar conexión de clientes - Ya no es necesario emitir tema inicial"""
    pass

@socketio.on('change_theme')
def handle_theme_change(data):
    """Manejar cambio de tema individual del usuario"""
    from flask import session
    from models.models import User

    # Verificar que el usuario está autenticado
    user_id = session.get('user_id')
    if not user_id:
        return {'success': False, 'message': 'No autenticado'}

    theme_name = data.get('theme')
    valid_themes = ['dark-turquoise', 'light-minimal', 'turquoise-gradient']

    if theme_name not in valid_themes:
        return {'success': False, 'message': 'Tema no válido'}

    # Guardar tema en el usuario actual (no en SystemConfig)
    user = User.query.get(user_id)
    if not user:
        return {'success': False, 'message': 'Usuario no encontrado'}

    user.theme_preference = theme_name
    db.session.commit()

    # Solo notificar al usuario actual (sin broadcast)
    emit('theme_update', {'theme': theme_name})

    return {'success': True, 'message': f'Tema cambiado a {theme_name}'}

def init_db():
    """Initialize database tables and run migrations"""
    with app.app_context():
        from models.models import User, TimeRecord
        # Si estamos en SQLite local, evita correr migraciones de Alembic
        try:
            driver = db.engine.url.drivername
        except Exception:
            driver = None

        if driver and driver.startswith("sqlite"):
            db.create_all()
            return

        # Para motores no-SQLite (p.ej., Postgres con datos reales), no tocar el esquema
        # para evitar problemas de dependencias o drivers en local. Asumimos que la BD ya
        # está provisionada (como la de Render descargada).
        return

def init_scheduler():
    """Initialize the background scheduler for automatic tasks"""
    if not SCHEDULER_AVAILABLE:
        app.logger.warning("APScheduler not available - automatic closing disabled")
        return

    try:
        scheduler = BackgroundScheduler(daemon=True)

        # Import the task functions
        from tasks.scheduler import auto_close_open_records
        from tasks.email_service_v3 import check_and_send_notifications_v3

        # Schedule the auto-close task to run daily at 23:59:59
        scheduler.add_job(
            func=auto_close_open_records,
            trigger=CronTrigger(hour=23, minute=59, second=59),
            id='auto_close_records',
            name='Auto-close open time records',
            replace_existing=True
        )

        # Schedule the email notification check to run every 5 minutes
        # USANDO VERSIÓN V3 con LOCK DISTRIBUIDO para prevenir duplicados en múltiples workers
        scheduler.add_job(
            func=lambda: check_and_send_notifications_v3(app, mail),
            trigger=CronTrigger(minute='*/5'),
            id='email_notifications_v3',
            name='Check and send email notifications V3 (with distributed lock)',
            replace_existing=True
        )

        scheduler.start()
        app.logger.info("Scheduler initialized - Auto-close task scheduled for 23:59:59 daily")
        app.logger.info("Scheduler initialized - Email notifications check every 5 minutes")

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
    except Exception as e:
        app.logger.error(f"Failed to initialize scheduler: {e}")
        app.logger.warning("Automatic closing disabled due to scheduler error")

if __name__ == '__main__':
    # Solo inicializar la base de datos cuando se ejecuta directamente (no con gunicorn)
    init_db()
    init_scheduler()
    port = int(os.getenv('PORT', 5000))
    # En producción usar debug=False
    debug_mode = not (os.getenv('DYNO') or os.getenv('RENDER'))
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)
else:
    # Cuando se ejecuta con gunicorn, inicializar la base de datos después de crear la app
    init_db()
    init_scheduler()
