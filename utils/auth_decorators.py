"""
Decoradores de autenticación y autorización centralizados.
Usado por múltiples blueprints para evitar duplicación y mantener
coherencia en verificación de permisos.
"""

from functools import wraps
from flask import session, redirect, url_for, flash
from models.models import User


def admin_required(f):
    """
    Decorador que requiere que el usuario sea administrador.
    Verifica tanto en sesión como en base de datos para mayor seguridad.

    Valida que el usuario:
    - Esté autenticado (tenga user_id en sesión)
    - Exista en la base de datos
    - Tenga rol 'admin' o 'super_admin'

    Si no cumple, limpia la sesión y redirige al login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = User.query.get(session.get("user_id"))
        # Verificar que el usuario tenga rol de admin o super_admin
        if not user or not user.role or user.role not in ('admin', 'super_admin'):
            session.clear()
            flash("Sin permisos de administrador.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
