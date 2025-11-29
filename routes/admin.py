from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from functools import wraps
from datetime import datetime, date, timedelta
from models.models import User, TimeRecord, EmployeeStatus, SystemConfig, LeaveRequest, WorkPause, Category, Center
from models.database import db
import plan_config  # Sistema de configuración multi-plan
from utils.multitenant import get_client_config

admin_bp = Blueprint(
    "admin", __name__,
    template_folder="../templates",
    url_prefix="/admin"
)

# Listas estáticas (DEPRECADAS - usar funciones dinámicas en su lugar)
CENTROS_DISPONIBLES = ["Centro 1", "Centro 2", "Centro 3"]
DEFAULT_CATEGORIES = ["Coordinador", "Empleado", "Gestor"]
CATEGORY_NONE_VALUES = {"sin categoria", "sin categoría", "-- sin categoría --"}

def get_categorias_disponibles():
    """
    Obtiene las categorías dinámicas del cliente actual desde la BD.
    Retorna una lista de nombres de categorías.
    IMPORTANTE: NO retorna valores hardcodeados, solo lo que está en la BD.
    """
    client_id = session.get("client_id")
    if not client_id:
        return []

    categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()
    return [c.name for c in categories]

def get_category_objects():
    """
    Obtiene los objetos Category del cliente actual desde la BD.
    Retorna una lista de objetos Category.
    """
    client_id = session.get("client_id")
    if not client_id:
        return []

    categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()
    return categories

def get_category_id_by_name(category_name):
    """
    Obtiene el ID de una categoría por su nombre.
    Retorna el ID o None si no existe.
    """
    if not category_name:
        return None

    client_id = session.get("client_id")
    if not client_id:
        return None

    category = Category.query.filter_by(client_id=client_id, name=category_name).first()
    return category.id if category else None


def parse_category_filter(value):
    """Devuelve (category_id, filter_none_flag) a partir del nombre enviado en filtros."""
    if not value or value in ("", "all"):
        return None, False

    normalized = value.strip().lower()
    if normalized in CATEGORY_NONE_VALUES:
        return None, True

    category_id = get_category_id_by_name(value)
    return category_id, False

def get_centros_dinamicos():
    """
    Obtiene los centros dinámicos del cliente actual desde la BD.
    Retorna una lista de nombres de centros.
    """
    client_id = session.get("client_id")
    if not client_id:
        return []

    centers = Center.query.filter_by(client_id=client_id, is_active=True).order_by(Center.name).all()
    if centers:
        return [c.name for c in centers]

    return []

def get_center_objects():
    """
    Obtiene los objetos Center del cliente actual desde la BD.
    Retorna una lista de objetos Center.
    """
    client_id = session.get("client_id")
    if not client_id:
        return []

    centers = Center.query.filter_by(client_id=client_id, is_active=True).order_by(Center.name).all()
    return centers

def get_center_id_by_name(center_name):
    """
    Obtiene el ID de un centro por su nombre.
    Retorna el ID o None si no existe.
    """
    if not center_name:
        return None

    client_id = session.get("client_id")
    if not client_id:
        return None

    center = Center.query.filter_by(client_id=client_id, name=center_name).first()
    return center.id if center else None

# --------------------------------------------------------------------
#  UTILIDADES
# --------------------------------------------------------------------
def admin_required(f):
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

# Centro del admin actual (None implica super admin con acceso global)

def get_admin_centro():
    """
    Obtiene el center_id del admin actual.
    - Super admin: retorna None (acceso global)
    - Admin de centro: retorna su center_id
    - Usuario normal: retorna None (no es admin)
    """
    uid = session.get("user_id")
    if not uid:
        return None
    u = User.query.get(uid)
    # Si no es admin, retornar None
    if not u or not is_admin_user(u):
        return None
    # Si es super admin, retornar None (acceso global)
    if is_super_admin_user(u):
        return None
    # Admin de centro: retornar su center_id
    if u.center_id:
        return u.center_id
    return None

def get_centros_disponibles():
    """
    Devuelve la lista de centros disponibles según el rol del admin (dinámicos desde BD).
    - Super admin: ve todos los centros del cliente
    - Admin de centro específico: solo ve su centro
    - Usuario normal: sin centros (no es admin)
    """
    u = _current_user()
    if not u or not is_admin_user(u):
        return []

    # Super admin: todos los centros dinámicos del cliente
    if is_super_admin_user(u):
        return get_centros_dinamicos()

    # Admin de centro: obtener su centro desde la BD
    if u.center:
        return [u.center.name]  # Retornar nombre del center desde la relación

    return []

# Helpers de permisos

def _current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None

def is_super_admin_user(u: User | None):
    """
    Verifica si un usuario es super admin.
    En LITE: no hay super admin (solo admin)
    En PRO: super_admin tiene acceso global
    """
    return bool(u and u.role == 'super_admin')

def is_admin_user(u: User | None):
    """
    Verifica si un usuario es admin (de centro o super admin).
    """
    return bool(u and u.role in ('admin', 'super_admin'))

def can_grant_admin():
    """
    Solo super_admin puede crear/asignar otros admins.
    En LITE: no se permite crear admins (solo el inicial).
    """
    u = _current_user()
    if not u or not is_super_admin_user(u):
        return False
    # Verificar que sea plan PRO
    client = u.client
    return client and client.plan == 'pro'

def can_grant_super_admin():
    """
    Solo super_admin en plan PRO puede crear otros super_admin.
    En LITE: no aplica (no hay super_admin).
    """
    u = _current_user()
    if not is_super_admin_user(u):
        return False
    client = u.client
    return client and client.plan == 'pro'

def format_timedelta(td):
    if td is None:
        return "-"
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}"

# --------------------------------------------------------------------
#  DASHBOARD
# --------------------------------------------------------------------
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    # Centro del admin (None => super admin con acceso global)
    centro_admin = get_admin_centro()

    # Filtros opcionales
    filtro_centro = request.args.get("centro", type=str, default="")
    filtro_categoria = request.args.get("categoria", type=str, default="")
    filtro_categoria_id, filtro_categoria_none = parse_category_filter(filtro_categoria)

    # Totales de usuarios (limitados por centro si aplica)
    # Empleados: usuarios sin rol admin
    user_q = User.query.filter(User.role.is_(None))
    if centro_admin:
        user_q = user_q.filter(User.center_id == centro_admin)
    elif filtro_centro:
        user_q = user_q.filter(User.center_id == filtro_centro)
    if filtro_categoria_id:
        user_q = user_q.filter(User.category_id == filtro_categoria_id)
    elif filtro_categoria_none:
        user_q = user_q.filter(User.category_id.is_(None))
    total_users = user_q.count()

    # Usuarios activos con fichaje abierto (limitados por centro si aplica)
    # Solo contar empleados (sin rol admin)
    active_q = (
        TimeRecord.query
        .join(User, TimeRecord.user_id == User.id)
        .filter(TimeRecord.check_in.isnot(None), TimeRecord.check_out.is_(None), User.role.is_(None))
        .with_entities(TimeRecord.user_id)
    )
    if centro_admin:
        active_q = active_q.filter(User.center_id == centro_admin)
    elif filtro_centro:
        active_q = active_q.filter(User.center_id == filtro_centro)
    if filtro_categoria_id:
        active_q = active_q.filter(User.category_id == filtro_categoria_id)
    elif filtro_categoria_none:
        active_q = active_q.filter(User.category_id.is_(None))
    active_users = active_q.distinct().count()

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    q = (
        TimeRecord.query
        .join(User, TimeRecord.user_id == User.id)
        .filter(
            TimeRecord.date >= start_of_week,
            TimeRecord.date <= end_of_week,
            User.role.is_(None)  # Solo empleados (sin rol admin)
        )
    )
    if centro_admin:
        q = q.filter(User.center_id == centro_admin)
    elif filtro_centro:
        q = q.filter(User.center_id == filtro_centro)
    if filtro_categoria_id:
        q = q.filter(User.category_id == filtro_categoria_id)
    elif filtro_categoria_none:
        q = q.filter(User.category_id.is_(None))

    records = q.order_by(TimeRecord.date.asc(), TimeRecord.check_in.asc()).all()

    week_acc, records_with_accum = {}, []
    for rec in records:
        uid = rec.user_id
        weekly_secs = rec.user.weekly_hours * 3600 if rec.user.weekly_hours else 0
        dur = rec.check_out - rec.check_in if rec.check_in and rec.check_out else None
        secs = dur.total_seconds() if dur else 0
        prev = week_acc.get(uid, 0)
        curr = prev + secs if rec.check_out else prev
        week_acc[uid] = curr
        rem = weekly_secs - curr

        # Buscar pausa activa del usuario si el registro está abierto
        active_pause = None
        if rec.check_in and not rec.check_out:
            active_pause = WorkPause.query.filter_by(
                user_id=uid,
                pause_end=None
            ).order_by(WorkPause.id.desc()).first()

        records_with_accum.append({
            "record": rec,
            "duration_formatted": format_timedelta(dur) if dur else "-",
            "remaining_formatted": format_timedelta(timedelta(seconds=abs(int(rem)))),
            "is_over": rem < 0,
            "is_open": rec.check_in and not rec.check_out,
            "active_pause": active_pause
        })

    records_with_accum.reverse()

    # Obtener centros disponibles según el rol del admin
    centros = get_centros_disponibles()
    categorias = get_categorias_disponibles()

    return render_template(
        "admin_dashboard.html",
        user_count=total_users,
        active_user_count=active_users,
        recent_records=records_with_accum,
        centros=centros,
        categorias=categorias
    )

# --------------------------------------------------------------------
#  USUARIOS
# --------------------------------------------------------------------
@admin_bp.route("/users")
@admin_required
def manage_users():
    centro_admin = get_admin_centro()

    # Verificar si es super admin (para saber si puede ver usuarios de otros clientes)
    is_super = is_super_admin_user(_current_user())

    # Filtros opcionales
    filtro_centro = request.args.get("centro", type=str, default="")
    filtro_categoria = request.args.get("categoria", type=str, default="")
    search_query = request.args.get("search", type=str, default="")

    q = User.query

    # Si es super admin, bypass el filtro multitenant para ver todos los usuarios
    if is_super:
        q = q.bypass_tenant_filter()

    if centro_admin:
        # Filtrar por ID de centro (el admin solo ve su centro)
        q = q.filter(User.center_id == centro_admin)
    elif filtro_centro:
        # Filtrar por nombre de centro dinámico
        q = q.join(Center, User.center_id == Center.id).filter(Center.name == filtro_centro)
    if filtro_categoria:
        # Filtrar por nombre de categoría a través de la relación
        q = q.join(Category, User.category_id == Category.id).filter(Category.name == filtro_categoria)
    if search_query:
        # Buscar en nombre completo (nombre y apellidos) y username
        q = q.filter(
            (User.full_name.ilike(f"%{search_query}%")) |
            (User.username.ilike(f"%{search_query}%"))
        )

    users = q.order_by(User.username).all()

    # Obtener centros disponibles según el rol del admin
    centros = get_centros_disponibles()
    categorias = get_categorias_disponibles()

    return render_template("manage_users.html", users=users, centros=centros, categorias=categorias, centro_admin=centro_admin)

@admin_bp.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    centro_admin = get_admin_centro()
    centros = get_centros_dinamicos()  # Centros dinámicos desde BD
    categorias = get_categorias_disponibles()
    client_id = session.get("client_id")

    # Determinar si el usuario actual puede asignar roles
    can_assign_admin = can_grant_admin()
    can_assign_super = can_grant_super_admin()
    can_assign_any_role = can_assign_admin or can_assign_super

    if not client_id:
        flash("No se pudo determinar el cliente activo.", "danger")
        return redirect(url_for("admin.manage_users"))
    client_config = get_client_config() or {}
    max_employees = client_config.get('max_employees', plan_config.MAX_EMPLOYEES)
    plan_messages = client_config.get('messages', plan_config.get_config().get('messages', {}))

    if request.method == "POST":
        username      = request.form.get("username")
        password      = request.form.get("password")
        full_name     = request.form.get("full_name")
        email         = request.form.get("email")
        # Solo algunos usuarios pueden crear administradores/super admin
        req_is_admin  = request.form.get("is_admin") == "on"
        weekly_hours  = request.form.get("weekly_hours", type=int)
        centro        = request.form.get("centro") or None
        categoria     = request.form.get("categoria") or None

        # Si el admin tiene un centro asignado, forzar que el usuario nuevo también lo tenga
        if centro_admin:
            centro = centro_admin

        # VALIDACIÓN DE LÍMITE DE EMPLEADOS (VERSION LITE)
        if max_employees is not None:
            # Contar empleados actuales (solo usuarios sin rol)
            query = User.query.filter_by(client_id=client_id).filter(User.role.is_(None))
            if centro:
                # Filtrar por centro dinámico usando join
                center_id = get_center_id_by_name(centro)
                if center_id:
                    query = query.filter_by(center_id=center_id)
            current_employee_count = query.count()

            # Verificar si se alcanzó el límite
            if current_employee_count >= max_employees:
                if plan_messages.get('employee_limit_reached'):
                    flash(plan_messages['employee_limit_reached'], "warning")
                if plan_messages.get('upgrade_prompt'):
                    flash(plan_messages['upgrade_prompt'], "info")
                return render_template("user_form.html", user=None, action="add",
                                       form_data=request.form, centro_admin=centro_admin,
                                       centros=centros, categorias=categorias)
        hire_date_str = request.form.get("hire_date")
        termination_date_str = request.form.get("termination_date")

        # Convertir fechas si están presentes
        hire_date = None
        termination_date = None
        try:
            if hire_date_str:
                hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
            if termination_date_str:
                termination_date = datetime.strptime(termination_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "danger")
            return render_template("user_form.html", user=None, action="add",
                                   form_data=request.form, centro_admin=centro_admin,
                                   centros=centros, categorias=categorias)
        # Obtener el rol solicitado del formulario
        # El formulario puede enviar: 'none', 'admin', 'super_admin', o no enviar nada
        requested_role_str = request.form.get("role", "none")

        # Determinar el rol final del nuevo usuario
        role = None  # Por defecto: empleado normal

        if requested_role_str == 'admin':
            # Si solicita admin, verificar permisos
            if can_grant_admin() or can_grant_super_admin():
                role = 'admin'
        elif requested_role_str == 'super_admin':
            # Si solicita super admin, verificar permisos específicos
            if can_grant_super_admin():
                role = 'super_admin'
                # Super admin no tiene centro específico
                centro = "-- Sin categoría --"
            else:
                flash("No tienes permisos para crear super admin.", "warning")

        if not all([username, password, full_name, email]) or weekly_hours is None:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("user_form.html", user=None, action="add",
                                   form_data=request.form, centro_admin=centro_admin,
                                   centros=centros, categorias=categorias)

        if User.query.filter(
            (User.client_id == client_id) &
            ((User.username == username) | (User.email == email))
        ).first():
            flash("El nombre de usuario o el correo electrónico ya existen.", "danger")
            return render_template("user_form.html", user=None, action="add",
                                   form_data=request.form, centro_admin=centro_admin,
                                   centros=centros, categorias=categorias)

        # Convertir el nombre de categoría a category_id y centro a center_id
        category_id = get_category_id_by_name(categoria)
        center_id = get_center_id_by_name(centro) if centro and centro != "-- Sin categoría --" else None

        new_user = User(
            client_id       = client_id,
            username         = username,
            full_name        = full_name,
            email            = email,
            role             = role,
            is_active        = True,
            weekly_hours     = weekly_hours,
            center_id        = center_id,
            category_id      = category_id,
            hire_date        = hire_date,
            termination_date = termination_date
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("admin.manage_users"))

    return render_template("user_form.html", user=None, action="add", centro_admin=centro_admin,
                           centros=centros, categorias=categorias,
                           can_assign_admin=can_assign_admin,
                           can_assign_super=can_assign_super,
                           can_assign_any_role=can_assign_any_role)

@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    centro_admin = get_admin_centro()
    centros = get_centros_dinamicos()  # Centros dinámicos desde BD
    categorias = get_categorias_disponibles()

    if request.method == "POST":
        if user.id == session.get("user_id") and (
            (request.form.get("is_admin")  == "on" and not user.is_admin) or
            (request.form.get("is_active") == "on" and not user.is_active)
        ):
            flash("No puedes cambiar tus propios permisos.", "danger")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        # Si el que edita no tiene permiso de conceder admin, ignorar cambios a is_admin
        requested_is_admin = (request.form.get("is_admin") == "on")
        if can_grant_admin():
            user.is_admin = requested_is_admin
        # Si no, se respeta el estado actual de user.is_admin sin cambios

        # username / email (únicos)
        new_username = request.form.get("username").strip()
        new_email    = request.form.get("email").strip()

        if new_username != user.username and \
           User.query.filter(User.username == new_username, User.id != user.id).first():
            flash("El nuevo nombre de usuario ya existe.", "danger")
            return render_template("user_form.html", user=user, action="edit",
                                   form_data=request.form, centro_admin=centro_admin,
                                   centros=centros, categorias=categorias)
        if new_email != user.email and \
           User.query.filter(User.email == new_email, User.id != user.id).first():
            flash("El nuevo correo electrónico ya existe.", "danger")
            return render_template("user_form.html", user=user, action="edit",
                                   form_data=request.form, centro_admin=centro_admin,
                                   centros=centros, categorias=categorias)

        # campos simples
        user.username      = new_username
        user.email         = new_email
        user.full_name     = request.form.get("full_name")
        user.weekly_hours  = request.form.get("weekly_hours", type=int)

        # Si el admin tiene un centro asignado, forzar que el usuario mantenga ese centro
        centro_name = None
        if centro_admin:
            centro_name = centro_admin
        else:
            centro_name = request.form.get("centro") or None

        # Usar FK dinámicamente
        user.center_id = get_center_id_by_name(centro_name) if centro_name and centro_name != "-- Sin categoría --" else None

        # Convertir el nombre de categoría a category_id
        categoria_name = request.form.get("categoria") or None
        user.category_id = get_category_id_by_name(categoria_name) if categoria_name else None

        # Fechas de alta y baja
        hire_date_str = request.form.get("hire_date")
        termination_date_str = request.form.get("termination_date")

        try:
            user.hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date() if hire_date_str else None
            user.termination_date = datetime.strptime(termination_date_str, "%Y-%m-%d").date() if termination_date_str else None
        except ValueError:
            flash("Formato de fecha inválido.", "danger")
            return render_template("user_form.html", user=user, action="edit",
                                   form_data=request.form, centro_admin=centro_admin,
                                   centros=centros, categorias=categorias)

        if user.id != session.get("user_id"):
            user.is_admin  = request.form.get("is_admin")  == "on"
            user.is_active = request.form.get("is_active") == "on"

        pw = request.form.get("password")
        if pw:
            user.set_password(pw)

        db.session.commit()
        flash("Usuario actualizado.", "success")
        return redirect(url_for("admin.manage_users"))

    return render_template("user_form.html", user=user, action="edit", centro_admin=centro_admin,
                           centros=centros, categorias=categorias)

@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get("user_id"):
        flash("No puedes eliminar tu propia cuenta.", "danger")
        return redirect(url_for("admin.manage_users"))

    # Limpiar referencias en system_config antes de borrar el usuario
    SystemConfig.query.filter_by(updated_by=user_id).update({"updated_by": None})

    db.session.delete(user)
    db.session.commit()
    flash("Usuario eliminado.", "success")
    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/users/toggle_active/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get("user_id"):
        flash("No puedes desactivar tu propia cuenta.", "danger")
        return redirect(url_for("admin.manage_users"))
    user.is_active = not user.is_active
    db.session.commit()
    flash(
        f"Usuario {user.username} {'activado' if user.is_active else 'desactivado'}.",
        "info"
    )
    return redirect(url_for("admin.manage_users"))

# --------------------------------------------------------------------
#  CATEGORÍAS
# ----

@admin_bp.route("/categories")
@admin_required
def manage_categories():
    """Listar categorías disponibles para el cliente actual"""
    client_id = session.get("client_id")
    if not client_id:
        flash("No se pudo determinar el cliente activo.", "danger")
        return redirect(url_for("admin.manage_users"))

    categories = Category.query.filter_by(client_id=client_id).order_by(Category.name).all()
    return render_template("manage_categories.html", categories=categories)


@admin_bp.route("/categories/add", methods=["GET", "POST"])
@admin_required
def add_category():
    """Agregar nueva categoría"""
    client_id = session.get("client_id")
    if not client_id:
        flash("No se pudo determinar el cliente activo.", "danger")
        return redirect(url_for("admin.manage_users"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("El nombre de la categoría es obligatorio.", "danger")
            return render_template("category_form.html", category=None, action="add")

        # Verificar que no existe una categoría con el mismo nombre para este cliente
        existing = Category.query.filter_by(client_id=client_id, name=name).first()
        if existing:
            flash(f"Ya existe una categoría con el nombre '{name}'.", "danger")
            return render_template("category_form.html", category=None, action="add")

        category = Category(
            client_id=client_id,
            name=name,
            description=description
        )
        db.session.add(category)
        db.session.commit()
        flash(f"Categoría '{name}' creada exitosamente.", "success")
        return redirect(url_for("admin.manage_categories"))

    return render_template("category_form.html", category=None, action="add")


@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):
    """Editar categoría"""
    category = Category.query.get_or_404(category_id)

    # Verificar que el usuario tenga permiso para editar esta categoría
    if category.client_id != session.get("client_id"):
        flash("No tienes permiso para editar esta categoría.", "danger")
        return redirect(url_for("admin.manage_categories"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("El nombre de la categoría es obligatorio.", "danger")
            return render_template("category_form.html", category=category, action="edit")

        # Verificar que no existe otra categoría con el mismo nombre para este cliente
        existing = Category.query.filter(
            Category.client_id == category.client_id,
            Category.name == name,
            Category.id != category_id
        ).first()
        if existing:
            flash(f"Ya existe otra categoría con el nombre '{name}'.", "danger")
            return render_template("category_form.html", category=category, action="edit")

        category.name = name
        category.description = description
        db.session.commit()
        flash(f"Categoría '{name}' actualizada exitosamente.", "success")
        return redirect(url_for("admin.manage_categories"))

    return render_template("category_form.html", category=category, action="edit")


@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@admin_required
def delete_category(category_id):
    """Eliminar categoría"""
    category = Category.query.get_or_404(category_id)

    # Verificar que el usuario tenga permiso para eliminar esta categoría
    if category.client_id != session.get("client_id"):
        flash("No tienes permiso para eliminar esta categoría.", "danger")
        return redirect(url_for("admin.manage_categories"))

    # Verificar que no hay usuarios usando esta categoría
    users_count = User.query.filter_by(category_id=category_id).count()
    if users_count > 0:
        flash(f"No puedes eliminar esta categoría porque está siendo utilizada por {users_count} usuario(s).", "danger")
        return redirect(url_for("admin.manage_categories"))

    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f"Categoría '{name}' eliminada.", "success")
    return redirect(url_for("admin.manage_categories"))


# ----
#  CENTROS
# ----

@admin_bp.route("/centers")
@admin_required
def manage_centers():
    """Listar centros disponibles para el cliente actual"""
    client_id = session.get("client_id")
    if not client_id:
        flash("No se pudo determinar el cliente activo.", "danger")
        return redirect(url_for("admin.manage_users"))

    centers = Center.query.filter_by(client_id=client_id).order_by(Center.name).all()
    return render_template("manage_centers.html", centers=centers)


@admin_bp.route("/centers/add", methods=["GET", "POST"])
@admin_required
def add_center():
    """Agregar nuevo centro"""
    client_id = session.get("client_id")
    if not client_id:
        flash("No se pudo determinar el cliente activo.", "danger")
        return redirect(url_for("admin.manage_users"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("El nombre del centro es obligatorio.", "danger")
            return render_template("center_form.html", center=None, action="add")

        # Verificar que no existe un centro con el mismo nombre para este cliente
        existing = Center.query.filter_by(client_id=client_id, name=name).first()
        if existing:
            flash(f"Ya existe un centro con el nombre '{name}'.", "danger")
            return render_template("center_form.html", center=None, action="add")

        center = Center(
            client_id=client_id,
            name=name,
            is_active=is_active
        )
        db.session.add(center)
        db.session.commit()
        flash(f"Centro '{name}' creado exitosamente.", "success")
        return redirect(url_for("admin.manage_centers"))

    return render_template("center_form.html", center=None, action="add")


@admin_bp.route("/centers/edit/<int:center_id>", methods=["GET", "POST"])
@admin_required
def edit_center(center_id):
    """Editar centro"""
    center = Center.query.get_or_404(center_id)

    # Verificar que el usuario tenga permiso para editar este centro
    if center.client_id != session.get("client_id"):
        flash("No tienes permiso para editar este centro.", "danger")
        return redirect(url_for("admin.manage_centers"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("El nombre del centro es obligatorio.", "danger")
            return render_template("center_form.html", center=center, action="edit")

        # Verificar que no existe otro centro con el mismo nombre para este cliente
        existing = Center.query.filter(
            Center.client_id == center.client_id,
            Center.name == name,
            Center.id != center_id
        ).first()
        if existing:
            flash(f"Ya existe otro centro con el nombre '{name}'.", "danger")
            return render_template("center_form.html", center=center, action="edit")

        center.name = name
        center.is_active = is_active
        db.session.commit()
        flash(f"Centro '{name}' actualizado exitosamente.", "success")
        return redirect(url_for("admin.manage_centers"))

    return render_template("center_form.html", center=center, action="edit")


@admin_bp.route("/centers/delete/<int:center_id>", methods=["POST"])
@admin_required
def delete_center(center_id):
    """Eliminar centro"""
    center = Center.query.get_or_404(center_id)

    # Verificar que el usuario tenga permiso para eliminar este centro
    if center.client_id != session.get("client_id"):
        flash("No tienes permiso para eliminar este centro.", "danger")
        return redirect(url_for("admin.manage_centers"))

    # Verificar que no hay usuarios usando este centro
    users_count = User.query.filter_by(center_id=center_id).count()
    if users_count > 0:
        flash(f"No puedes eliminar este centro porque está siendo utilizado por {users_count} usuario(s).", "danger")
        return redirect(url_for("admin.manage_centers"))

    name = center.name
    db.session.delete(center)
    db.session.commit()
    flash(f"Centro '{name}' eliminado.", "success")
    return redirect(url_for("admin.manage_centers"))


# ----
#  REGISTROS
# ----
@admin_bp.route("/records")
@admin_required
def manage_records():
    # Página actual (semana): 1 = esta semana, 2 = anterior, etc.
    page = request.args.get("page", type=int, default=1)
    today = date.today()
    # Lunes de la semana actual
    start_of_current = today - timedelta(days=today.weekday())
    # Calcular la semana a mostrar según el número de página
    week_offset = (page - 1) * 7
    start_of_week = start_of_current - timedelta(days=week_offset)
    end_of_week = start_of_week + timedelta(days=6)

    # Calcular número de semana ISO y rango de días
    week_number = start_of_week.isocalendar().week

    # Nombres de meses en español
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    mes_nombre = meses_es[start_of_week.month]
    week_range = f"{start_of_week.day} - {end_of_week.day} de {mes_nombre}"

    # Filtros por query params (fecha, hora, categoría, centro y búsqueda)
    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")
    time_from = request.args.get("time_from")  # HH:MM
    time_to   = request.args.get("time_to")    # HH:MM
    categoria = request.args.get("categoria")
    filtro_centro = request.args.get("centro", type=str, default="")
    search_query = request.args.get("search", type=str, default="")

    # Buscar registros solo de esa semana + filtros
    q = (
        TimeRecord.query
        .join(User, TimeRecord.user_id == User.id)
        .filter(
            TimeRecord.date >= start_of_week,
            TimeRecord.date <= end_of_week,
            User.role.is_(None),  # Solo empleados (sin rol admin)
            TimeRecord.check_out.isnot(None)
        )
    )

    # Scope por centro del admin, si aplica. Si es super admin, permitir filtro por centro
    centro_admin = get_admin_centro()
    if centro_admin:
        q = q.filter(User.center_id == centro_admin)
    elif filtro_centro:
        q = q.filter(User.center_id == filtro_centro)

    # Aplicar filtros opcionales (fechas)
    ci_from = co_to = None
    try:
        if date_from:
            df = datetime.strptime(date_from, "%Y-%m-%d").date()
            q = q.filter(TimeRecord.date >= df)
        if date_to:
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            q = q.filter(TimeRecord.date <= dt)
        if time_from:
            ci_from = datetime.strptime(time_from, "%H:%M").time()
        if time_to:
            co_to = datetime.strptime(time_to, "%H:%M").time()
    except ValueError:
        flash("Formato de fecha/hora inválido en filtros.", "warning")

    if categoria:
        # Filtrar por nombre de categoría a través de la relación
        q = q.join(Category, User.category_id == Category.id).filter(Category.name == categoria)
    
    # Filtrar por búsqueda de nombre completo y username
    if search_query:
        q = q.filter(
            (User.full_name.ilike(f"%{search_query}%")) | 
            (User.username.ilike(f"%{search_query}%"))
        )

    recs = q.order_by(TimeRecord.user_id, TimeRecord.date.asc(), TimeRecord.check_in.asc()).all()

    # Filtrar por horas en Python para compatibilidad con SQLite/Postgres
    if ci_from or co_to:
        filtered = []
        for r in recs:
            ok = True
            if ci_from and (not r.check_in or r.check_in.time() < ci_from):
                ok = False
            if co_to and (not r.check_out or r.check_out.time() > co_to):
                ok = False
            if ok:
                filtered.append(r)
        recs = filtered

    # Lógica de acumulados (igual que antes)
    weekly_acc = {}
    enriched = []
    for rec in recs:
        uid = rec.user_id
        # Lunes de la semana correspondiente
        sow = rec.date - timedelta(days=rec.date.weekday())
        sow_str = sow.strftime('%Y-%m-%d')
        wh_secs = rec.user.weekly_hours * 3600 if rec.user.weekly_hours else 0

        if uid not in weekly_acc:
            weekly_acc[uid] = {}
        if sow_str not in weekly_acc[uid]:
            weekly_acc[uid][sow_str] = 0

        dur = rec.check_out - rec.check_in if rec.check_in and rec.check_out else None
        secs = dur.total_seconds() if dur else 0

        weekly_acc[uid][sow_str] += secs
        curr_week_total = weekly_acc[uid][sow_str]
        rem = wh_secs - curr_week_total

        enriched.append({
            "record": rec,
            "duration_formatted": format_timedelta(dur),
            "remaining": format_timedelta(timedelta(seconds=abs(int(rem)))),
            "is_over": rem < 0
        })

    # ¿Hay una semana anterior en la base de datos?
    earliest_record = TimeRecord.query.order_by(TimeRecord.date.asc()).first()
    has_next = False
    if earliest_record:
        first_week = earliest_record.date - timedelta(days=earliest_record.date.weekday())
        has_next = start_of_week > first_week

    # Mostramos la semana más reciente primero
    enriched = enriched[::-1]

    # Calcular si es la semana actual
    is_current_week = (start_of_week == start_of_current)

    # Obtener centros disponibles según el rol del admin
    centros = get_centros_disponibles()
    categorias = get_categorias_disponibles()

    return render_template(
        "manage_records.html",
        records=enriched,
        page=page,
        has_next=has_next,
        week_number=week_number,
        week_range=week_range,
        is_current_week=is_current_week,
        centros=centros,
        categorias=categorias,
        centro_admin=centro_admin
    )

@admin_bp.route("/records/edit/<int:record_id>", methods=["GET", "POST"])
@admin_required
def edit_record(record_id):
    record = TimeRecord.query.get_or_404(record_id)
    page = request.args.get("page", type=int, default=1)
    if request.method == "POST":
        try:
            ds = request.form.get("date")
            ci = request.form.get("check_in")
            co = request.form.get("check_out")

            record.date      = datetime.strptime(ds, "%Y-%m-%d").date()
            record.check_in  = datetime.strptime(f"{ds} {ci}", "%Y-%m-%d %H:%M:%S") if ci else None
            record.check_out = datetime.strptime(f"{ds} {co}", "%Y-%m-%d %H:%M:%S") if co else None
            # NO modificar record.notes - esas son solo del empleado
            record.admin_notes = request.form.get("admin_notes")
            record.modified_by = session.get("user_id")

            if record.check_in and record.check_out and record.check_out < record.check_in:
                flash("La salida no puede ser anterior a la entrada.", "danger")
                return render_template("record_form.html", record=record,
                                       form_data=request.form)

            db.session.commit()
            flash("Registro actualizado.", "success")
            return redirect(url_for("admin.manage_records", page=page, edited=record.id))

        except ValueError:
            flash("Formato fecha/hora inválido.", "danger")
    return render_template("record_form.html", record=record, page=page)

@admin_bp.route("/records/delete/<int:record_id>", methods=["POST"])
@admin_required
def delete_record(record_id):
    record = TimeRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Registro eliminado.", "success")
    return redirect(url_for("admin.manage_records"))

# --------------------------------------------------------------------
#  CALENDARIO GLOBAL + API 
# --------------------------------------------------------------------
@admin_bp.route("/calendar")
@admin_required
def admin_calendar():
    # Pasamos el centro del admin (None => super admin)
    # Pasar centros dinámicos desde BD
    centros = get_centros_disponibles()
    return render_template("admin_calendar.html", centro_admin=get_admin_centro(), centros=centros)

@admin_bp.route("/api/events")
@admin_required
def api_events():
    """Eventos para el calendario global."""
    user_id = request.args.get("user_id", type=int)
    start   = request.args.get("start")
    end     = request.args.get("end")
    status  = request.args.get("status")
    centro  = request.args.get("centro")

    STATUS_GROUPS = {
        "Trabajado": ["Trabajado"],
        "Baja": ["Baja"],
        "Ausente": ["Ausente"],
        "Vacaciones": ["Vacaciones"]
    }
    STATUS_ALIAS = {s: group for group, values in STATUS_GROUPS.items() for s in values}

    # ==== Cambios para manejo correcto de fechas ====
    start_date = None
    end_date = None

    # Si no hay fechas, usar el mes actual como rango por defecto
    today = date.today()

    if start:
        try:
            if 'T' in start:
                start_date = datetime.fromisoformat(start.replace('Z', '')).date()
            else:
                start_date = datetime.strptime(start, "%Y-%m-%d").date()
        except Exception:
            start_date = None

    if end:
        try:
            if 'T' in end:
                end_date = datetime.fromisoformat(end.replace('Z', '')).date()
            else:
                end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except Exception:
            end_date = None

    # Si no hay rango de fechas, usar el mes actual
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        # Último día del mes actual
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    q = EmployeeStatus.query.join(User).filter(User.role.is_(None))  # Solo empleados

    # Scope por centro del admin (si tiene asignado)
    centro_admin = get_admin_centro()
    if centro_admin:
        # Filtrar por centro dinámico usando center_id
        # centro_admin es ya un center_id (INTEGER), no un nombre
        q = q.filter(User.center_id == centro_admin)
    elif centro:
        # Si no hay centro del admin, permitir filtrar por parámetro opcional
        # Filtrar por centro dinámico usando center_id
        center_id = get_center_id_by_name(centro)
        if center_id:
            q = q.filter(User.center_id == center_id)

    if user_id:
        q = q.filter(EmployeeStatus.user_id == user_id)
    if start_date:
        q = q.filter(EmployeeStatus.date >= start_date)
    if end_date:
        q = q.filter(EmployeeStatus.date <= end_date)
    if status:
        status_values = STATUS_GROUPS.get(status, [status])
        q = q.filter(EmployeeStatus.status.in_(status_values))

    # Mapa de colores completo (incluye tipos de solicitud específicos)
    color_map = {
        "Trabajado" : "#60a5fa",                    # Azul
        "Baja"      : "#f87171",                    # Rojo
        "Baja médica": "#f87171",                   # Rojo (igual a Baja)
        "Ausente"   : "#fbbf24",                    # Amarillo
        "Vacaciones": "#34d399",                    # Verde claro
        "Ausencia justificada": "#fbbf24",          # Amarillo (igual a Ausente)
        "Ausencia injustificada": "#ef4444",        # Rojo oscuro
        "Permiso especial": "#15803d"               # Verde oscuro
    }

    events = []
    for es in q.all():
        # Determinar color: si hay request_type, usarlo; si no, usar status
        color_key = es.request_type if es.request_type else es.status
        color = color_map.get(color_key, "#9ca3af")

        # Buscar TimeRecord del mismo día para pre-rellenar horas en el modal
        tr = TimeRecord.query.filter_by(user_id=es.user_id, date=es.date).first()
        check_in_time = tr.check_in.strftime("%H:%M:%S") if tr and tr.check_in else None
        check_out_time = tr.check_out.strftime("%H:%M:%S") if tr and tr.check_out else None

        events.append({
            "id": es.id,
            "title": f"{es.status} - {es.user.full_name or es.user.username}",
            "start": es.date.isoformat(),
            "color": color,
            "extendedProps": {
                "notes": es.notes,
                "admin_notes": es.admin_notes,  # Incluir notas del admin
                "username": es.user.full_name or es.user.username,
                "category": es.user.category.name if es.user.category else "-",
                "filterStatus": STATUS_ALIAS.get(es.status, es.status),
                "check_in_time": check_in_time,
                "check_out_time": check_out_time
            },
            "allDay": True
        })
    return jsonify(events)

@admin_bp.route("/api/employees")
@admin_required
def api_employees():
    centro = request.args.get("centro")
    query = User.query.filter(User.role.is_(None))  # Solo empleados (sin rol admin)

    # Limitar por centro del admin, si aplica (super admin => None)
    centro_admin = get_admin_centro()
    if centro_admin:
        # Filtrar por centro dinámico usando center_id
        # centro_admin es ya un center_id (INTEGER), no un nombre
        query = query.filter(User.center_id == centro_admin)
    elif centro:
        # Filtrar por centro dinámico usando center_id
        center_id = get_center_id_by_name(centro)
        if center_id:
            query = query.filter(User.center_id == center_id)

    employees = query.order_by(User.full_name).all()
    return jsonify([
        {"id": u.id, "username": u.username, "full_name": u.full_name}
        for u in employees
    ])

@admin_bp.route("/api/centro_info")
@admin_required
def api_centro_info():
    centro = request.args.get("centro")
    users = User.query.filter_by(is_admin=False)

    centro_admin = get_admin_centro()
    if centro_admin:
        users = users.filter(User.center_id == centro_admin)
    elif centro:
        users = users.filter(User.center_id == centro)

    users = users.all()
    # Obtener categorías dinámicas del cliente actual (no hardcodeadas)
    categorias = get_categorias_disponibles()
    horas = sorted(set(u.weekly_hours for u in users if u.weekly_hours is not None))
    return jsonify({
        "usuarios": [{"id": u.id, "username": u.username, "full_name": u.full_name} for u in users],
        "categorias": categorias,
        "horas": horas
    })

# --------------------------------------------------------------------
#  FICHA INDIVIDUAL (rangos fechas)
# --------------------------------------------------------------------
@admin_bp.route("/employees/<int:user_id>/status", methods=["GET", "POST"])
@admin_required
def manage_employee_status(user_id):
    """
    Alta / actualización de estados del empleado.
    • Se admite rango de fechas (start_date / end_date)
    • Solo se guarda 'status' + 'notes'  → sin categoría
    • Si ya existe un estado para ese día, se sobreescribe
    """
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        start_str = request.form.get("start_date")
        end_str   = request.form.get("end_date") or start_str
        status    = request.form.get("status", "")
        admin_notes = request.form.get("admin_notes", "")  # Admin escribe en admin_notes

        if not start_str:
            flash("Indica la fecha de inicio.", "danger")
            return redirect(url_for("admin.manage_employee_status", user_id=user_id))

        try:
            start = datetime.strptime(start_str, "%Y-%m-%d").date()
            end   = datetime.strptime(end_str,   "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "danger")
            return redirect(url_for("admin.manage_employee_status", user_id=user_id))

        if end < start:
            flash("La fecha final no puede ser anterior a la inicial.", "danger")
            return redirect(url_for("admin.manage_employee_status", user_id=user_id))

        delta = (end - start).days + 1
        for i in range(delta):
            day = start + timedelta(days=i)
            existing = EmployeeStatus.query.filter_by(
                user_id=user_id, date=day
            ).first()
            if existing:
                existing.status = status
                existing.admin_notes = admin_notes  # Guardar en admin_notes, no en notes
            else:
                client_id = session.get("client_id", 1)  # Multi-tenant
                db.session.add(EmployeeStatus(
                    client_id = client_id,
                    user_id = user_id,
                    date    = day,
                    status  = status,
                    admin_notes = admin_notes  # Guardar en admin_notes, no en notes
                ))
        db.session.commit()
        flash("Estado guardado.", "success")
        return redirect(url_for("admin.manage_employee_status", user_id=user_id))

    return render_template("employee_status.html", user=user)

# --------------------------------------------------------------------
#  ELIMINAR ESTADO INDIVIDUAL DE UN EMPLEADO
# --------------------------------------------------------------------
@admin_bp.route("/employees/<int:user_id>/status/delete/<int:status_id>", methods=["POST"])
@admin_required
def delete_employee_status(user_id, status_id):
    status = EmployeeStatus.query.get_or_404(status_id)
    db.session.delete(status)
    db.session.commit()
    flash("Estado eliminado correctamente.", "success")
    return redirect(url_for("admin.manage_employee_status", user_id=user_id))

@admin_bp.route("/employees/<int:user_id>/status/edit/<int:status_id>", methods=["POST"])
@admin_required
def edit_employee_status(user_id, status_id):
    status = EmployeeStatus.query.get_or_404(status_id)
    data = request.get_json()

    # Actualizar estado y notas del admin
    status.status = data.get("status")
    status.admin_notes = data.get("admin_notes")  # Admin escribe en admin_notes

    # Manejo de horas de entrada/salida (TimeRecord)
    check_in = (data.get("check_in") or "").strip()
    check_out = (data.get("check_out") or "").strip()

    def parse_time(t):
        if not t:
            return None
        try:
            # soporta HH:MM o HH:MM:SS
            fmt = "%H:%M:%S" if len(t.split(":")) == 3 else "%H:%M"
            tm = datetime.strptime(t, fmt).time()
            return tm
        except Exception:
            return None

    ci_time = parse_time(check_in)
    co_time = parse_time(check_out)

    # Crear/actualizar/eliminar TimeRecord del día
    tr = TimeRecord.query.filter_by(user_id=user_id, date=status.date).first()
    if ci_time or co_time:
        if not tr:
            tr = TimeRecord(
                client_id=status.client_id,
                user_id=user_id,
                date=status.date
            )
            db.session.add(tr)
        if ci_time:
            tr.check_in = datetime.combine(status.date, ci_time)
        else:
            tr.check_in = None
        if co_time:
            tr.check_out = datetime.combine(status.date, co_time)
        else:
            tr.check_out = None
        # Si el admin ha escrito notas en el modal, guardarlas también en el TimeRecord
        if data.get("admin_notes") is not None:
            tr.admin_notes = data.get("admin_notes") or None

        # Validación simple: salida no antes que entrada
        if tr.check_in and tr.check_out and tr.check_out < tr.check_in:
            db.session.rollback()
            return jsonify({"ok": False, "error": "La salida no puede ser anterior a la entrada."}), 400
    else:
        # Si no hay horas y existe un TimeRecord, lo eliminamos
        if tr:
            db.session.delete(tr)

    db.session.commit()
    return jsonify({"ok": True})

# --------------------------------------------------------------------
#  FICHAS ABIERTAS DE EMPLEADOS
# --------------------------------------------------------------------
@admin_bp.route("/open_records", methods=["GET", "POST"])
@admin_required
def open_records():
    # Limitar por centro del admin si aplica y excluir admins
    centro_admin = get_admin_centro()
    q = (
        TimeRecord.query
        .join(User, TimeRecord.user_id == User.id)
        .filter(
            TimeRecord.check_in.isnot(None),
            TimeRecord.check_out.is_(None),
            User.role.is_(None)  # Solo empleados
        )
    )
    if centro_admin:
        q = q.filter(User.center_id == centro_admin)
    open_records = q.all()

    if request.method == "POST":
        record_id = request.form.get("record_id")
        close_time = request.form.get("close_time")
        record = TimeRecord.query.get(record_id)
        if record and close_time:
            try:
                record.check_out = datetime.strptime(close_time, "%Y-%m-%dT%H:%M")
                db.session.commit()
                flash("Registro cerrado correctamente.", "success")
            except Exception as e:
                flash(f"Error al cerrar: {e}", "danger")
        return redirect(url_for("admin.open_records"))

    # Pasar la hora actual para usarla como valor predeterminado
    now = datetime.now()
    return render_template("open_records.html", open_records=open_records, now=now)

# --------------------------------------------------------------------
#  CIERRE AUTOMÁTICO MANUAL
# --------------------------------------------------------------------
@admin_bp.route("/close_today_records", methods=["POST"])
@admin_required
def close_today_records():
    """Manual trigger to close all open records for today"""
    try:
        from tasks.scheduler import manual_auto_close_records
        from datetime import datetime
        closed_count = manual_auto_close_records()
        if closed_count > 0:
            current_time = datetime.now().strftime('%H:%M')
            flash(f"Se cerraron {closed_count} registros abiertos de hoy a las {current_time}.", "success")
        else:
            flash("No hay registros abiertos para cerrar hoy.", "info")
    except ImportError:
        flash("La funcionalidad de cierre automático no está disponible.", "warning")
    except Exception as e:
        flash(f"Error al cerrar registros: {str(e)}", "danger")

    return redirect(url_for("admin.open_records"))


# --------------------------------------------------------------------
#  GESTIÓN DE SOLICITUDES DE IMPUTACIONES
# --------------------------------------------------------------------
@admin_bp.route("/leave_requests")
@admin_required
def leave_requests():
    """Ver y gestionar solicitudes de vacaciones/bajas/ausencias"""
    centro_admin = get_admin_centro()

    # Obtener filtros de la URL
    filter_centro = request.args.get("centro", "all")
    filter_categoria = request.args.get("categoria", "all")
    filter_categoria_id, filter_categoria_none = parse_category_filter(
        filter_categoria if filter_categoria != "all" else ""
    )
    filter_categoria_id, filter_categoria_none = parse_category_filter(
        filter_categoria if filter_categoria != "all" else ""
    )
    filter_categoria_id, filter_categoria_none = parse_category_filter(
        filter_categoria if filter_categoria != "all" else ""
    )
    filter_categoria_id, filter_categoria_none = parse_category_filter(
        filter_categoria if filter_categoria != "all" else ""
    )
    filter_usuario = request.args.get("usuario", "")

    # Navegación por fechas
    filter_date = request.args.get("date", date.today().isoformat())

    try:
        filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
    except ValueError:
        filter_date = date.today()

    # Obtener todas las solicitudes pendientes (incluye "Pendiente" y "Enviado")
    query = (
        LeaveRequest.query
        .join(User, LeaveRequest.user_id == User.id)
        .filter(LeaveRequest.status.in_(["Pendiente", "Enviado"]))
    )

    # Aplicar filtros
    if centro_admin:
        query = query.filter(User.center_id == centro_admin)
    elif filter_centro != "all":
        query = query.filter(User.center_id == filter_centro)

    if filter_categoria_id:
        query = query.filter(User.category_id == filter_categoria_id)
    elif filter_categoria_none:
        query = query.filter(User.category_id.is_(None))

    if filter_usuario:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{filter_usuario}%"),
                User.username.ilike(f"%{filter_usuario}%")
            )
        )

    pending_requests = query.order_by(LeaveRequest.created_at.desc()).all()

    # Marcar solicitudes de bajas/ausencias como "Recibido" cuando el admin las ve
    leave_types = ["Baja médica", "Ausencia justificada", "Ausencia injustificada"]
    for leave_req in pending_requests:
        if leave_req.request_type in leave_types and leave_req.status == "Enviado":
            leave_req.status = "Recibido"
            leave_req.read_by_admin = True
            leave_req.read_date = datetime.now()

    # Guardar cambios si hubo actualizaciones
    try:
        db.session.commit()
    except:
        db.session.rollback()

    # Obtener historial de solicitudes procesadas para la fecha filtrada
    history_query = (
        LeaveRequest.query
        .join(User, LeaveRequest.user_id == User.id)
        .filter(LeaveRequest.status.in_(["Aprobado", "Rechazado", "Cancelado", "Recibido"]))
    )

    # Aplicar filtros al historial
    if centro_admin:
        history_query = history_query.filter(User.center_id == centro_admin)
    elif filter_centro != "all":
        history_query = history_query.filter(User.center_id == filter_centro)

    if filter_categoria_id:
        history_query = history_query.filter(User.category_id == filter_categoria_id)
    elif filter_categoria_none:
        history_query = history_query.filter(User.category_id.is_(None))

    if filter_usuario:
        history_query = history_query.filter(
            db.or_(
                User.full_name.ilike(f"%{filter_usuario}%"),
                User.username.ilike(f"%{filter_usuario}%")
            )
        )

    # Filtrar histórico por el día seleccionado
    history_query = history_query.filter(
        db.func.date(LeaveRequest.created_at) == filter_date
    )

    history_requests = history_query.order_by(
        LeaveRequest.updated_at.desc()
    ).all()

    # Calcular fechas de navegación
    prev_date = (filter_date - timedelta(days=1)).isoformat()
    next_date = (filter_date + timedelta(days=1)).isoformat()
    today_iso = date.today().isoformat()
    is_today = filter_date == date.today()

    # Obtener lista de centros y categorías para los filtros
    centros = get_centros_disponibles()
    categorias = get_categorias_disponibles()

    return render_template(
        "admin_leave_requests.html",
        pending_requests=pending_requests,
        history_requests=history_requests,
        centros=centros,
        categorias=categorias,
        filter_centro=filter_centro,
        filter_categoria=filter_categoria,
        filter_usuario=filter_usuario,
        filter_date=filter_date,
        prev_date=prev_date,
        next_date=next_date,
        today_iso=today_iso,
        is_today=is_today,
        centro_admin=centro_admin
    )


@admin_bp.route("/leave_requests/approve/<int:request_id>", methods=["POST"])
@admin_required
def approve_leave_request(request_id):
    """Aprobar una solicitud de imputación"""
    # Detectar si es una llamada AJAX (desde la campanita) o formulario tradicional
    is_ajax = request.headers.get('Accept', '').find('application/json') != -1

    try:
        centro_admin = get_admin_centro()
        admin_id = session.get("user_id")

        # Buscar la solicitud
        leave_request = LeaveRequest.query.get_or_404(request_id)

        # Verificar permisos
        if centro_admin:
            user = User.query.get(leave_request.user_id)
            if user.center_id != centro_admin:
                if is_ajax:
                    return jsonify({"success": False, "error": "No tienes permisos para aprobar esta solicitud."}), 403
                flash("No tienes permisos para aprobar esta solicitud.", "danger")
                return redirect(url_for("admin.leave_requests"))

        # Aprobar la solicitud
        leave_request.status = "Aprobado"
        leave_request.approved_by = admin_id
        leave_request.approval_date = datetime.now()

        # Guardar notas del admin si las proporciona
        admin_notes = request.form.get("admin_notes")
        if admin_notes:
            leave_request.admin_notes = admin_notes

        # Crear EmployeeStatus para los días solicitados
        status_map = {
            "Vacaciones": "Vacaciones",
            "Baja médica": "Baja",
            "Ausencia justificada": "Ausente",
            "Ausencia injustificada": "Ausente",
            "Permiso especial": "Vacaciones"
        }

        status = status_map.get(leave_request.request_type, "Ausente")
        current_date = leave_request.start_date

        while current_date <= leave_request.end_date:
            # Verificar si ya existe un status para ese día
            existing_status = EmployeeStatus.query.filter_by(
                user_id=leave_request.user_id,
                date=current_date
            ).first()

            if existing_status:
                existing_status.status = status
                existing_status.request_type = leave_request.request_type
                existing_status.notes = f"Solicitud aprobada: {leave_request.request_type}"
                if admin_notes:
                    existing_status.admin_notes = admin_notes
            else:
                new_status = EmployeeStatus(
                    client_id=leave_request.client_id,  # Multi-tenant: obtener de la solicitud
                    user_id=leave_request.user_id,
                    date=current_date,
                    status=status,
                    request_type=leave_request.request_type,
                    notes=f"Solicitud aprobada: {leave_request.request_type}",
                    admin_notes=admin_notes if admin_notes else None
                )
                db.session.add(new_status)

            current_date += timedelta(days=1)

        db.session.commit()

        # Responder según el tipo de petición
        if is_ajax:
            return jsonify({"success": True, "message": f"Solicitud de {leave_request.request_type} aprobada correctamente."})

        flash(f"Solicitud de {leave_request.request_type} aprobada correctamente.", "success")

    except Exception as e:
        db.session.rollback()
        if is_ajax:
            return jsonify({"success": False, "error": str(e)}), 500
        flash(f"Error al aprobar la solicitud: {str(e)}", "danger")

    return redirect(url_for("admin.leave_requests"))


@admin_bp.route("/leave_requests/reject/<int:request_id>", methods=["POST"])
@admin_required
def reject_leave_request(request_id):
    """Rechazar una solicitud de imputación"""
    # Detectar si es una llamada AJAX (desde la campanita) o formulario tradicional
    is_ajax = request.headers.get('Accept', '').find('application/json') != -1

    try:
        centro_admin = get_admin_centro()
        admin_id = session.get("user_id")

        # Buscar la solicitud
        leave_request = LeaveRequest.query.get_or_404(request_id)

        # Verificar permisos
        if centro_admin:
            user = User.query.get(leave_request.user_id)
            if user.center_id != centro_admin:
                if is_ajax:
                    return jsonify({"success": False, "error": "No tienes permisos para rechazar esta solicitud."}), 403
                flash("No tienes permisos para rechazar esta solicitud.", "danger")
                return redirect(url_for("admin.leave_requests"))

        # Obtener motivo de rechazo si viene en el body (desde AJAX)
        reason = None
        if is_ajax and request.is_json:
            data = request.get_json()
            reason = data.get('reason', '')

        # Rechazar la solicitud
        leave_request.status = "Rechazado"
        leave_request.approved_by = admin_id
        leave_request.approval_date = datetime.now()

        # Guardar motivo de rechazo en admin_notes si existe
        if reason:
            leave_request.admin_notes = f"Rechazado: {reason}"

        # También guardar admin_notes del formulario si vienen
        admin_notes = request.form.get("admin_notes")
        if admin_notes:
            leave_request.admin_notes = admin_notes

        db.session.commit()

        # Responder según el tipo de petición
        if is_ajax:
            return jsonify({"success": True, "message": f"Solicitud de {leave_request.request_type} rechazada correctamente."})

        flash(f"Solicitud de {leave_request.request_type} rechazada.", "info")

    except Exception as e:
        db.session.rollback()
        if is_ajax:
            return jsonify({"success": False, "error": str(e)}), 500
        flash(f"Error al rechazar la solicitud: {str(e)}", "danger")

    return redirect(url_for("admin.leave_requests"))


@admin_bp.route("/work_pauses")
@admin_required
def work_pauses():
    """Ver pausas/descansos de los empleados"""
    centro_admin = get_admin_centro()

    # Obtener filtros desde la URL
    filter_date = request.args.get("date", date.today().isoformat())
    filter_centro = request.args.get("centro", "all")
    filter_categoria = request.args.get("categoria", "all")
    filter_usuario = request.args.get("usuario", "")
    filter_categoria_id, filter_categoria_none = parse_category_filter(
        filter_categoria if filter_categoria != "all" else ""
    )

    try:
        filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
    except ValueError:
        filter_date = date.today()

    # Buscar pausas del día filtrado
    query = (
        WorkPause.query
        .join(User, WorkPause.user_id == User.id)
        .join(TimeRecord, WorkPause.time_record_id == TimeRecord.id)
        .filter(TimeRecord.date == filter_date)
    )

    # Si es admin de centro, filtrar por centro
    if centro_admin:
        query = query.filter(User.center_id == centro_admin)
        filter_centro = centro_admin
    elif filter_centro != "all" and filter_centro:
        query = query.filter(User.center_id == filter_centro)

    if filter_categoria_id:
        query = query.filter(User.category_id == filter_categoria_id)
    elif filter_categoria_none:
        query = query.filter(User.category_id.is_(None))

    if filter_usuario:
        like = f"%{filter_usuario}%"
        query = query.filter(
            db.or_(
                User.full_name.ilike(like),
                User.username.ilike(like)
            )
        )

    pauses = query.order_by(WorkPause.pause_start.desc()).all()

    # Calcular estadísticas
    total_pauses = len(pauses)
    active_pauses = sum(1 for p in pauses if p.pause_end is None)

    # Calcular tiempo total de pausas
    total_pause_time = timedelta()
    for pause in pauses:
        if pause.pause_end:
            total_pause_time += pause.pause_end - pause.pause_start
        else:
            # Para pausas activas, calcular hasta ahora
            total_pause_time += datetime.now() - pause.pause_start

    prev_date = (filter_date - timedelta(days=1)).isoformat()
    next_date = (filter_date + timedelta(days=1)).isoformat()
    today_iso = date.today().isoformat()
    is_today = filter_date == date.today()

    centros = get_centros_disponibles()

    return render_template(
        "admin_work_pauses.html",
        pauses=pauses,
        filter_date=filter_date,
        total_pauses=total_pauses,
        active_pauses=active_pauses,
        total_pause_time=format_timedelta(total_pause_time),
        prev_date=prev_date,
        next_date=next_date,
        today_iso=today_iso,
        is_today=is_today,
        centros=centros,
        categorias=get_categorias_disponibles(),
        filter_centro=filter_centro,
        filter_categoria=filter_categoria,
        filter_usuario=filter_usuario,
        centro_admin=centro_admin
    )


# --------------------------------------------------------------------
#  NOTIFICACIONES DE BAJAS AUTO-APROBADAS
# --------------------------------------------------------------------
@admin_bp.route("/notifications/leaves")
@admin_required
def get_leave_notifications():
    """Obtener notificaciones de bajas médicas y ausencias auto-aprobadas"""
    centro_admin = get_admin_centro()

    # Obtener bajas auto-aprobadas de los últimos 7 días
    since_date = date.today() - timedelta(days=7)

    query = (
        LeaveRequest.query
        .join(User, LeaveRequest.user_id == User.id)
        .filter(
            LeaveRequest.status == "Aprobado",
            LeaveRequest.request_type.in_(["Baja médica", "Ausencia justificada", "Ausencia injustificada"]),
            LeaveRequest.created_at >= since_date,
            LeaveRequest.approved_by.is_(None)  # Auto-aprobadas (sin admin que las apruebe)
        )
    )

    # Filtrar por centro si aplica
    if centro_admin:
        query = query.filter(User.center_id == centro_admin)

    notifications = query.order_by(LeaveRequest.created_at.desc()).limit(20).all()

    notifications_data = []
    for notif in notifications:
        days_count = (notif.end_date - notif.start_date).days + 1
        notifications_data.append({
            "id": notif.id,
            "employee_name": notif.user_rel.full_name,
            "employee_username": notif.user_rel.username,
            "request_type": notif.request_type,
            "start_date": notif.start_date.strftime("%d/%m/%Y"),
            "end_date": notif.end_date.strftime("%d/%m/%Y"),
            "days_count": days_count,
            "reason": notif.reason or "Sin motivo especificado",
            "created_at": notif.created_at.strftime("%d/%m/%Y %H:%M"),
            "is_recent": (datetime.now() - notif.created_at).total_seconds() < 1800,  # Últimos 30 minutos
            "has_attachment": notif.attachment_url is not None,
            "attachment_url": notif.attachment_url,
            "attachment_filename": notif.attachment_filename,
            "attachment_type": notif.attachment_type
        })

    return jsonify({
        "success": True,
        "notifications": notifications_data,
        "count": len(notifications_data)
    })

@admin_bp.route("/notifications/pending-requests")
@admin_required
def get_pending_requests():
    """Obtener solicitudes pendientes agrupadas por tipo"""
    centro_admin = get_admin_centro()

    # Consultar solicitudes pendientes o enviadas (no procesadas)
    query = (
        LeaveRequest.query
        .join(User, LeaveRequest.user_id == User.id)
        .filter(
            LeaveRequest.status.in_(["Enviado", "Pendiente"])
        )
    )

    # Filtrar por centro si aplica
    if centro_admin:
        query = query.filter(User.center_id == centro_admin)

    requests = query.order_by(LeaveRequest.created_at.desc()).all()

    # Agrupar por tipo
    vacaciones = []
    bajas = []
    ausencias = []

    for req in requests:
        days_count = (req.end_date - req.start_date).days + 1
        request_data = {
            "id": req.id,
            "employee_name": req.user_rel.full_name or req.user_rel.username,
            "employee_username": req.user_rel.username,
            "request_type": req.request_type,
            "start_date": req.start_date.strftime("%d/%m/%Y"),
            "end_date": req.end_date.strftime("%d/%m/%Y"),
            "days_count": days_count,
            "reason": req.reason or "Sin motivo especificado",
            "created_at": req.created_at.strftime("%d/%m/%Y %H:%M"),
            "status": req.status,
            "has_attachment": req.attachment_url is not None,
            "attachment_url": req.attachment_url,
            "attachment_filename": req.attachment_filename
        }

        # Clasificar por tipo
        if req.request_type == "Vacaciones":
            vacaciones.append(request_data)
        elif req.request_type == "Baja médica":
            bajas.append(request_data)
        elif req.request_type in ["Ausencia justificada", "Ausencia injustificada", "Permiso especial"]:
            ausencias.append(request_data)

    return jsonify({
        "success": True,
        "vacaciones": vacaciones,
        "bajas": bajas,
        "ausencias": ausencias,
        "total": len(requests),
        "counts": {
            "vacaciones": len(vacaciones),
            "bajas": len(bajas),
            "ausencias": len(ausencias)
        }
    })
