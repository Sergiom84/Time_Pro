"""
Decoradores de autenticación y autorización centralizados.
Usado por múltiples blueprints para evitar duplicación y mantener
coherencia en verificación de permisos.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
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


def client_required(f):
    """
    Decorador que requiere client_id válido en sesión.
    Inyecta client_id como parámetro a la función decorada.

    Valida que:
    - El usuario esté autenticado
    - Tenga client_id en la sesión

    Si falta client_id:
    - Para peticiones JSON (APIs): retorna 401 JSON
    - Para peticiones HTML: redirige al login con mensaje flash

    Ejemplo de uso:
        @app.route("/check_in", methods=["POST"])
        @client_required
        def check_in(client_id):
            # client_id fue inyectado automáticamente
            record = TimeRecord(client_id=client_id, ...)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = session.get("client_id")
        if not client_id:
            # Detectar si es petición JSON (API) o el cliente espera JSON (FormData con AJAX)
            wants_json = request.is_json or (
                request.accept_mimetypes
                and request.accept_mimetypes.accept_json
                and request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']
            )
            if wants_json:
                return jsonify({
                    "success": False,
                    "error": "No se pudo determinar el cliente activo. Inicia sesión nuevamente."
                }), 401
            else:
                flash("No se pudo determinar tu empresa. Inicia sesión nuevamente.", "danger")
                return redirect(url_for("auth.login"))

        # Inyectar client_id en kwargs para que la función lo reciba
        kwargs['client_id'] = client_id
        return f(*args, **kwargs)
    return decorated_function
