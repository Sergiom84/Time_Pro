import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models.database import db
from models.models import User, Client

app = Flask(__name__)

# Use the same SQLite file as the app
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sqlite_uri = 'sqlite:///' + os.path.join(basedir, 'timetracker.db')
app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'seed_admins_secret'

db.init_app(app)

DEFAULT_CLIENT_IDENTIFIER = os.getenv("SEED_CLIENT", "1")

def resolve_client_id(identifier: str) -> int:
    """
    Resolve client_id from numeric id or slug/name.
    Falls back to 1 for legacy single-tenant setups.
    """
    with app.app_context():
        if not hasattr(User, 'client_id'):
            return 1
        client = None
        if identifier.isdigit():
            client = Client.query.filter_by(id=int(identifier)).first()
        if client is None:
            client = Client.query.filter_by(slug=identifier.lower()).first()
        if client is None:
            client = Client.query.filter(Client.name.ilike(identifier)).first()
        if client:
            return client.id
        # default bootstrap client
        client = Client.query.filter_by(id=1).first()
        if client:
            return client.id
        # create default
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

TARGET_CLIENT_ID = resolve_client_id(DEFAULT_CLIENT_IDENTIFIER)

ADMINS = [
    {"username": "Mercedes",  "full_name": "Mercedes",  "email": "mercedes@example.com",  "centro": "Avenida de Brasil"},
    {"username": "Valentina", "full_name": "Valentina", "email": "valentina@example.com", "centro": "Las Tablas"},
    {"username": "Juan",      "full_name": "Juan",      "email": "juan@example.com",      "centro": "Majadahonda"},
    {"username": "Lorena",    "full_name": "Lorena",    "email": "lorena@example.com",    "centro": "Hortaleza"},
]

DEFAULT_PASSWORD = "2025"


def upsert_admin(uinfo):
    query = User.query
    if hasattr(User, 'client_id'):
        query = query.filter_by(client_id=TARGET_CLIENT_ID)
    user = query.filter_by(username=uinfo["username"]).first()
    if user is None:
        user = User(
            client_id=TARGET_CLIENT_ID if hasattr(User, 'client_id') else None,
            username=uinfo["username"],
            full_name=uinfo["full_name"],
            email=uinfo["email"],
            is_admin=True,
            is_active=True,
            weekly_hours=40,  # default
            centro=uinfo["centro"],
        )
        user.set_password(DEFAULT_PASSWORD)
        db.session.add(user)
        action = "created"
    else:
        user.full_name = uinfo["full_name"]
        user.email = uinfo["email"]
        user.is_admin = True
        user.is_active = True
        user.centro = uinfo["centro"]
        user.set_password(DEFAULT_PASSWORD)
        action = "updated"
    return user, action


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        results = []
        for info in ADMINS:
            user, action = upsert_admin(info)
            results.append((user.username, action, user.centro))
        db.session.commit()

        for username, action, centro in results:
            print(f"{username}: {action} (centro: {centro})")
        print("Done.")

