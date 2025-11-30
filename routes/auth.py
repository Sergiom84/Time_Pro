from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.security import check_password_hash
from models.models import User, Client
from models.database import db
from utils.logging_utils import mask_dsn, get_logger

auth_bp = Blueprint("auth", __name__)  # Usa la carpeta global de templates

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        client_identifier = (request.form.get("client_identifier") or "").strip()

        if not client_identifier:
            flash("Debes indicar el identificador de tu empresa.", "danger")
            return render_template("login.html", client_identifier=client_identifier)

        client = None
        if client_identifier.isdigit():
            client = Client.query.filter_by(id=int(client_identifier)).first()
        if client is None:
            client = Client.query.filter_by(slug=client_identifier.lower()).first()
        if client is None:
            client = Client.query.filter(Client.name.ilike(client_identifier)).first()

        if not client or not client.is_active:
            flash("No encontramos una empresa activa con ese identificador.", "danger")
            return render_template("login.html", client_identifier=client_identifier)

        try:
            # Debug: registrar motor y URL efectiva sin credenciales
            from sqlalchemy import text
            logger = get_logger(__name__)
            logger.debug(f"[LOGIN] engine: {db.engine.url.drivername} url: {mask_dsn(str(db.engine.url))}")
            # Probar una consulta trivial a Postgres para forzar el bind real
            db.session.execute(text("SELECT 1"))
            logger.debug("[LOGIN] SELECT 1 ok")
        except Exception as e:
            logger.debug(f"[LOGIN] connection-test error: {e}")
        try:
            user = User.query.filter_by(client_id=client.id, username=username).first()
        except Exception as e:
            # Registrar detalles del engine si la query falla
            try:
                logger.debug(f"[LOGIN] on-query engine: {db.engine.url.drivername} url: {mask_dsn(str(db.engine.url))}")
            except Exception:
                pass
            raise

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["is_admin"] = user.role is not None  # True si tiene algún rol (admin o super_admin)
            session["client_id"] = user.client_id  # Multi-tenant: guardar client_id
            # Guardar el centro del admin si está asignado
            if user.role and user.center_id:
                session["admin_center_id"] = user.center_id
            else:
                session["admin_center_id"] = None
            # No mostramos flash de "Inicio de sesión exitoso" para evitar mensajes residuales
            if user.role:  # Si tiene algún rol (admin o super_admin)
                return redirect(url_for("admin.dashboard"))
            else:
                # Ahora apuntamos directamente al dashboard de time.py
                return redirect(url_for("time.dashboard_employee"))
        else:
            flash("Nombre de usuario o contraseña incorrectos.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("is_admin", None)
    session.pop("admin_center_id", None)
    session.pop("client_id", None)  # Multi-tenant: limpiar client_id
    # Asegurar que no queden flashes anteriores (p.ej., "inicio de sesión exitoso")
    session.pop("_flashes", None)
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/registro", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username         = request.form.get("username")
        full_name        = request.form.get("full_name")
        email            = request.form.get("email")
        password         = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        client_identifier = (request.form.get("client_identifier") or "").strip()

        if not client_identifier:
            flash("Debes indicar el identificador de la empresa para registrarte.", "danger")
            return redirect(url_for("auth.register"))

        client = None
        if client_identifier.isdigit():
            client = Client.query.filter_by(id=int(client_identifier)).first()
        if client is None:
            client = Client.query.filter_by(slug=client_identifier.lower()).first()
        if client is None:
            client = Client.query.filter(Client.name.ilike(client_identifier)).first()

        if not client or not client.is_active:
            flash("No encontramos una empresa activa con ese identificador.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("auth.register"))

        # Multi-tenant: Verificar username y email por cliente
        if User.query.filter_by(client_id=client.id, username=username).first():
            flash("El nombre de usuario ya existe.", "danger")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(client_id=client.id, email=email).first():
            flash("El email ya está registrado.", "danger")
            return redirect(url_for("auth.register"))

        nuevo_usuario = User(
            client_id=client.id,
            username=username,
            full_name=full_name,
            email=email,
            role='admin'  # usuario que se registra pasa a ser administrador del cliente
        )
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# ================================================================
#  API: Obtener información del cliente actual
# ================================================================
@auth_bp.route("/api/current-client", methods=["GET"])
def get_current_client():
    """Retorna la información del cliente actual (incluyendo logo)"""
    if "client_id" not in session:
        return jsonify({"error": "No autenticado"}), 401

    client_id = session.get("client_id")
    client = Client.query.get(client_id)

    if not client:
        return jsonify({"error": "Cliente no encontrado"}), 404

    return jsonify({
        "id": client.id,
        "name": client.name,
        "slug": client.slug,
        "plan": client.plan,
        "logo_url": client.logo_url,
        "primary_color": client.primary_color,
        "secondary_color": client.secondary_color,
        "is_active": client.is_active
    })

from utils.auth_decorators import admin_required
