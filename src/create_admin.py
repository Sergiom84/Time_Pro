import sys
import os

# Añadir la carpeta raíz del proyecto al path para permitir imports relativos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.models import User, Client
from models.database import db
from flask import Flask

app = Flask(__name__)

# Usar SQLite local (mismo timetracker.db que utiliza main.py)
basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_uri = 'sqlite:///' + os.path.join(basedir, '..', 'timetracker.db')
app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'temporal_secret'

# Inicializar SQLAlchemy ANTES del contexto
db.init_app(app)

DEFAULT_CLIENT_IDENTIFIER = os.getenv("CREATE_ADMIN_CLIENT", "1")

def resolve_client_id(identifier: str) -> int | None:
    if not hasattr(User, 'client_id'):
        return None
    client = None
    if identifier.isdigit():
        client = Client.query.filter_by(id=int(identifier)).first()
    if client is None:
        client = Client.query.filter_by(slug=identifier.lower()).first()
    if client is None:
        client = Client.query.filter(Client.name.ilike(identifier)).first()
    if client:
        return client.id
    client = Client.query.filter_by(id=1).first()
    if client:
        return client.id
    client = Client(
        id=1,
        name="Time Pro",
        slug="time-pro",
        plan="pro",
        is_active=True
    )
    db.session.add(client)
    db.session.commit()
    return client.id

with app.app_context():
    db.create_all()

    target_client_id = resolve_client_id(DEFAULT_CLIENT_IDENTIFIER)

    query = User.query
    if target_client_id is not None:
        query = query.filter_by(client_id=target_client_id)

    existing = query.filter_by(username='admin').first()

    if not existing:
        user = User(
            client_id=target_client_id,
            username='admin',
            full_name='Administrador',
            email='admin@example.com',
            is_admin=True,
            is_active=True
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        print(f"✅ Usuario admin creado para client_id={target_client_id or 'legacy'}")
    else:
        print("ℹ️ Ya existe un usuario 'admin' para este cliente.")
