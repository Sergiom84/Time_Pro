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

from flask import Flask, render_template, request, abort, jsonify
from flask_mail import Mail
from flask_caching import Cache
from flask_talisman import Talisman
from flask_compress import Compress
from models.database import db
from flask_migrate import Migrate, upgrade as migrate_upgrade
from routes.auth import auth_bp
from routes.time import time_bp
from routes.admin import admin_bp
from routes.export import export_bp
import plan_config  # Sistema de configuración multi-plan
from utils.logging_utils import mask_dsn, get_logger
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    import atexit
    SCHEDULER_AVAILABLE = True
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"APScheduler not available: {e}")
    SCHEDULER_AVAILABLE = False

# Versión de arranque para diagnóstico de despliegues
APP_VERSION = "2025-11-28-2"

# Crear instancia de la app Flask
app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)

# Configuración general
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or os.urandom(24).hex()
# Endure CSRF/CSWSH mitigations via cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('PREFER_SECURE_COOKIES', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True

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

logger = get_logger(__name__)
logger.info(f"Using database: {mask_dsn(app.config['SQLALCHEMY_DATABASE_URI'])}")

#########################
# Seguridad HTTP
#########################

# Configurar Flask-Talisman para cabeceras de seguridad
force_https = os.getenv('FORCE_HTTPS', 'False').lower() == 'true'
Talisman(
    app,
    content_security_policy=None,  # CSP desactivada por ahora para no romper recursos
    force_https=force_https
)

# Habilitar compresión gzip para respuestas HTTP
# Reduce tamaño de respuestas en ~70% (HTML, JSON, CSS)
Compress(app)

# Configure SQLAlchemy engine options based on environment
is_production = os.getenv('DYNO') or os.getenv('RENDER')
if is_production:
    # Production environment - reduced pooling for eventlet + 1 worker
    # Con eventlet + 1 worker no necesitamos 30 conexiones (pool_size + max_overflow)
    # Configurado para usar Connection Pooler (puerto 6543)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 3,        # Reducido de 10 a 3
        "max_overflow": 7,     # Reducido de 20 a 7 (total: 10 conexiones)
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

# Inicializar cache en memoria simple (suficiente para 1 worker eventlet)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Logging de queries lentas (> 1 segundo) para detectar cuellos de botella
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Log queries > 1 segundo
        app.logger.warning(f"⚠️ Slow query ({total:.2f}s): {statement[:200]}")

# Log de diagnóstico para confirmar columnas efectivas en el modelo User en tiempo de ejecución
try:
    from models.models import User
    logger.info(f"Time_Pro version {APP_VERSION} loaded")
    logger.debug(f"User columns at startup: {[c.name for c in User.__table__.columns]}")
except Exception as e:
    logger.warning(f"Could not log User columns at startup: {e}")

# Configurar filtrado automático multi-tenant
from utils.multitenant import setup_multitenant_filters
with app.app_context():
    setup_multitenant_filters(app, db)

# Log rápido del driver efectivo
try:
    with app.app_context():
        logger.debug(f"Database driver: {db.engine.url.drivername}")
except Exception:
    pass

# Log de diagnóstico por request para confirmar motor/URL
@app.before_request
def _log_db_on_request():
    try:
        logger.debug(
            f"[REQ] {request.method} {request.path} -> "
            f"engine={db.engine.url.drivername} url={mask_dsn(str(db.engine.url))}"
        )
    except Exception as e:
        logger.debug(f"[REQ] engine-info error: {e}")

# Memory profiling opcional (solo en debug mode)
import tracemalloc

@app.before_request
def _memory_profiling_start():
    if app.debug:
        tracemalloc.start()

@app.after_request
def _memory_profiling_end(response):
    if app.debug and tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        app.logger.info(f"💾 Memory: {current / 10**6:.2f}MB (peak: {peak / 10**6:.2f}MB) - {request.path}")
        tracemalloc.stop()
    return response

migrate = Migrate(app, db)

# Proper session cleanup
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Rechazar peticiones mutables desde orígenes no permitidos (mitiga CSRF/CSWSH)
@app.before_request
def _enforce_origin_for_state_changing():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("Origin")
        if origin:
            origin_norm = origin.rstrip('/')
            host_norm = request.host_url.rstrip('/')
            if origin_norm != host_norm and origin_norm not in _allowed_origins:
                abort(403)

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

    # Cachear el contexto por 5 minutos para evitar 3 queries en cada request
    if user_id:
        cache_key = f"user_context_{user_id}"
        cached = cache.get(cache_key)

        if cached:
            return cached

    if user_id:
        user = db.session.get(User, user_id)
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

    # Tema por defecto
    current_theme = 'dark-turquoise'

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

    result = dict(
        current_user=user,
        greeting=greeting,
        current_theme=current_theme,
        plan_config=plan_config_dict,
        current_client=current_client,
        client_config=client_config_dict
    )

    # Guardar en cache por 5 minutos
    if user_id:
        cache_key = f"user_context_{user_id}"
        cache.set(cache_key, result, timeout=300)

    return result

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

    # En producción con múltiples workers (Gunicorn), solo el worker principal debe ejecutar el scheduler
    # Esto evita tareas duplicadas
    worker_id = os.getenv('GUNICORN_WORKER_ID', '0')
    is_render = os.getenv('RENDER', False)

    # Solo ejecutar scheduler en:
    # 1. Desarrollo (sin Gunicorn)
    # 2. Worker 0 en producción
    if is_render and worker_id != '0':
        app.logger.info(f"Worker {worker_id} - Skipping scheduler initialization (only worker 0 runs scheduler)")
        return

    try:
        scheduler = BackgroundScheduler(daemon=True)

        # Import the task functions and initialize with app reference
        from tasks.scheduler import auto_close_open_records, init_scheduler_app
        from tasks.email_service_v3 import check_and_send_notifications_v3

        # IMPORTANTE: Pasar la referencia de la app al módulo de scheduler
        # Esto evita el error "Working outside of application context"
        init_scheduler_app(app)

        # Schedule the auto-close task to run daily at 23:59:59
        scheduler.add_job(
            func=auto_close_open_records,
            trigger=CronTrigger(hour=23, minute=59, second=59),
            id='auto_close_records',
            name='Auto-close open time records',
            replace_existing=True
        )

        # Schedule the email notification check to run every 5 minutes (optional)
        # USANDO VERSIÓN V3 con LOCK DISTRIBUIDO para prevenir duplicados en múltiples workers
        scheduler.add_job(
            func=lambda: None,  # email notifications disabled
            trigger=CronTrigger(minute='*/5'),
            id='email_notifications_v3',
            name='Check and send email notifications V3 (with distributed lock)',
            replace_existing=True
        )

        scheduler.start()
        app.logger.info(f"✓ Scheduler initialized on worker {worker_id} - Auto-close task scheduled for 23:59:59 daily")
        app.logger.info("✓ Scheduler initialized - Email notifications check every 5 minutes")

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
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
else:
    # Cuando se ejecuta con gunicorn, inicializar la base de datos después de crear la app
    init_db()
    init_scheduler()
