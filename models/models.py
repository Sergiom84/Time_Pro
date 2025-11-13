from .database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index


class Client(db.Model):
    """Modelo para gestionar clientes/empresas (multi-tenant)"""
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)  # Ej: "Aluminios Lara"
    slug = db.Column(db.String(100), unique=True, nullable=False)  # Ej: "aluminios-lara"
    plan = db.Column(
        db.Enum("lite", "pro", name="plan_enum"),
        nullable=False,
        default="pro"
    )
    logo_url = db.Column(db.String(500), nullable=True)  # URL del logo en Supabase
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Configuración de branding
    primary_color = db.Column(db.String(7), default="#0ea5e9")  # Color principal (hex)
    secondary_color = db.Column(db.String(7), default="#06b6d4")  # Color secundario

    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    users = db.relationship("User", backref="client", lazy=True, cascade="all, delete-orphan")
    categories = db.relationship("Category", backref="client", lazy=True, cascade="all, delete-orphan")
    centers = db.relationship("Center", backref="client", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.name} ({self.plan})>"


class Category(db.Model):
    """Modelo para categorías de empleados (dinámicas por cliente)"""
    __tablename__ = "category"
    __table_args__ = (
        db.UniqueConstraint("client_id", "name", name="uix_client_category_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Ej: "Camarero", "Cocinero"
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Category {self.name} (client_id={self.client_id})>"


class Center(db.Model):
    """Modelo para centros/sucursales (dinámicos por cliente)"""
    __tablename__ = "center"
    __table_args__ = (
        db.UniqueConstraint("client_id", "name", name="uix_client_center_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # Ej: "Centro 1", "Aluminios Lara"
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Center {self.name} (client_id={self.client_id})>"


class User(db.Model):
    __tablename__ = "user"
    __table_args__ = (
        db.UniqueConstraint("client_id", "username", name="uix_client_username"),
        db.UniqueConstraint("client_id", "email", name="uix_client_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(
        db.Enum("admin", "super_admin", name="role_enum"),
        nullable=True,
        default=None
    )  # null=usuario normal, 'admin'=admin de centro, 'super_admin'=admin global
    is_active = db.Column(db.Boolean, default=True)
    weekly_hours = db.Column(db.Integer, nullable=False, default=0)
    centro = db.Column(
        db.Enum(
            "-- Sin categoría --", "Centro 1", "Centro 2", "Centro 3", "Aluminios Lara", "La esquina del paisa",
            name="centro_enum"
        ),
        nullable=True
    )
    center_id = db.Column(db.Integer, db.ForeignKey("center.id", ondelete="SET NULL"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="SET NULL"), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    termination_date = db.Column(db.Date, nullable=True)
    theme_preference = db.Column(db.String(50), default='dark-turquoise', nullable=False)

    # Campos para notificaciones por correo
    email_notifications = db.Column(db.Boolean, default=False, nullable=False)
    notification_days = db.Column(db.String(100), nullable=True)  # Formato: "L,M,X,J,V"
    notification_time_entry = db.Column(db.Time, nullable=True)  # Hora de aviso para entrada
    notification_time_exit = db.Column(db.Time, nullable=True)   # Hora de aviso para salida
    additional_notification_email = db.Column(db.String(120), nullable=True)  # Correo adicional para notificaciones

    # Campos para rastrear notificaciones enviadas y evitar duplicados
    last_entry_notification_sent = db.Column(db.DateTime, nullable=True)  # Última notificación de entrada enviada
    last_exit_notification_sent = db.Column(db.DateTime, nullable=True)   # Última notificación de salida enviada

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    center = db.relationship("Center", backref="users", lazy=True)
    category = db.relationship("Category", backref="users", lazy=True)

    time_records = db.relationship(
        "TimeRecord",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="TimeRecord.user_id"
    )

    statuses = db.relationship(
        "EmployeeStatus",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class TimeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    modified_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<TimeRecord {self.id}-U{self.user_id}>"

class EmployeeStatus(db.Model):
    __tablename__ = "employee_status"
    __table_args__ = (
        db.UniqueConstraint("client_id", "user_id", "date", name="uix_employee_date"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.Enum(
            "Trabajado", "Baja", "Ausente", "Vacaciones",
            name="status_enum"
        ),
        nullable=False,
        default=""
    )
    notes = db.Column(db.Text, nullable=True)
    request_type = db.Column(db.String(50), nullable=True)  # Tipo de solicitud original (Vacaciones, Baja médica, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<EmployeeStatus {self.id}-U{self.user_id} "
            f"{self.date} {self.status}>"
        )


class WorkPause(db.Model):
    """Modelo para registrar pausas/descansos durante la jornada laboral"""
    __tablename__ = "work_pause"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    time_record_id = db.Column(db.Integer, db.ForeignKey("time_record.id", ondelete="CASCADE"), nullable=False)
    pause_type = db.Column(
        db.Enum(
            "Descanso", "Hora del almuerzo", "Asuntos médicos",
            "Desplazamientos", "Otros",
            name="pause_type_enum"
        ),
        nullable=False
    )
    pause_start = db.Column(db.DateTime, nullable=False)
    pause_end = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Campos para archivos adjuntos
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)
    attachment_size = db.Column(db.Integer, nullable=True)

    # Relaciones
    user_rel = db.relationship("User", backref="work_pauses", lazy=True)
    time_record_rel = db.relationship("TimeRecord", backref="pauses", lazy=True)

    def __repr__(self):
        return f"<WorkPause {self.id} - {self.pause_type}>"


class LeaveRequest(db.Model):
    """Modelo para solicitudes de vacaciones, bajas y ausencias"""
    __tablename__ = "leave_request"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    request_type = db.Column(
        db.Enum(
            "Vacaciones", "Baja médica", "Ausencia justificada",
            "Ausencia injustificada", "Permiso especial",
            name="leave_type_enum"
        ),
        nullable=False
    )
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(
            "Pendiente", "Aprobado", "Rechazado", "Cancelado", "Enviado", "Recibido",
            name="request_status_enum"
        ),
        nullable=False,
        default="Pendiente"
    )
    approved_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    read_by_admin = db.Column(db.Boolean, default=False, nullable=False)
    read_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Campos para archivos adjuntos
    attachment_url = db.Column(db.String(500), nullable=True)
    attachment_filename = db.Column(db.String(255), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)
    attachment_size = db.Column(db.Integer, nullable=True)

    # Relaciones
    user_rel = db.relationship("User", foreign_keys=[user_id], backref="leave_requests", lazy=True)
    approver_rel = db.relationship("User", foreign_keys=[approved_by], backref="approved_requests", lazy=True)

    def __repr__(self):
        return f"<LeaveRequest {self.id} - {self.request_type} - {self.status}>"


class SystemConfig(db.Model):
    """Modelo para almacenar configuración del sistema"""
    __table_args__ = (
        db.UniqueConstraint("client_id", "key", name="uix_client_key"),
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    key = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))

    @classmethod
    def get_theme(cls, client_id):
        """Obtiene el tema actual del sistema para un cliente"""
        config = cls.query.filter_by(client_id=client_id, key='theme').first()
        if config:
            return config.value
        return 'dark-turquoise'  # Tema por defecto

    @classmethod
    def set_theme(cls, client_id, theme_name, user_id=None):
        """Establece el tema del sistema para un cliente"""
        config = cls.query.filter_by(client_id=client_id, key='theme').first()
        if not config:
            config = cls(
                client_id=client_id,
                key='theme',
                value=theme_name,
                description='Tema visual del sistema'
            )
            db.session.add(config)
        else:
            config.value = theme_name

        if user_id:
            config.updated_by = user_id
        config.updated_at = datetime.utcnow()
        db.session.commit()
        return config

    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value}>"
