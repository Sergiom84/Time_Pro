import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_mail import Mail
from models.database import db
from flask_migrate import Migrate, upgrade as migrate_upgrade
from routes.auth import auth_bp
from routes.time import time_bp
from routes.admin import admin_bp
from routes.export import export_bp
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

# Configuración de la base de datos
# Usando Supabase como base de datos principal
# La contraseña contiene un @ que necesita ser URL-encoded
from urllib.parse import quote_plus

supabase_password = "OPt0u_oag6Pir5MR0@"
supabase_password_encoded = quote_plus(supabase_password)

supabase_dsn = (
    f"postgresql://postgres.gqesfclbingbihakiojm:"
    f"{supabase_password_encoded}@"
    f"aws-1-eu-west-1.pooler.supabase.com:6543/"
    f"postgres"
)

# Configuración de Supabase (para futuro uso si necesitas API)
SUPABASE_URL = "https://gqesfclbingbihakiojm.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxZXNmY2xiaW5nYmloYWtpb2ptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4Mjc2NzEsImV4cCI6MjA3NzQwMzY3MX0.FmhKu9LVids3b0cs7Q0GssEvjJcEOCkVifalx1bzxgY"

uri = os.getenv("DATABASE_URL") or supabase_dsn
# Normalizar si viniera como postgres://
uri = uri.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_DATABASE_URI'] = uri
print("Usando BD:", app.config['SQLALCHEMY_DATABASE_URI'], file=sys.stderr)

# Configure SQLAlchemy engine options based on environment
is_production = os.getenv('DYNO') or os.getenv('RENDER')
if is_production:
    # Production environment - standard pooling for sync workers
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30
    }
else:
    # Development environment - use default pooling
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 20,
        "max_overflow": 0
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

# Context processor para hacer disponible el usuario actual y saludo
@app.context_processor
def inject_user():
    from flask import session
    from models.models import User, SystemConfig
    from datetime import datetime

    user = None
    greeting = ""

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

    # Obtener el tema actual del usuario (si está autenticado) o el tema por defecto
    if user:
        current_theme = user.theme_preference
    else:
        current_theme = 'dark-turquoise'  # Tema por defecto para usuarios no autenticados

    return dict(current_user=user, greeting=greeting, current_theme=current_theme)

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(time_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(export_bp)

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
        from tasks.email_service import check_and_send_notifications

        # Schedule the auto-close task to run daily at 23:59:59
        scheduler.add_job(
            func=auto_close_open_records,
            trigger=CronTrigger(hour=23, minute=59, second=59),
            id='auto_close_records',
            name='Auto-close open time records',
            replace_existing=True
        )

        # Schedule the email notification check to run every 5 minutes
        scheduler.add_job(
            func=lambda: check_and_send_notifications(app, mail),
            trigger=CronTrigger(minute='*/5'),
            id='email_notifications',
            name='Check and send email notifications',
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
