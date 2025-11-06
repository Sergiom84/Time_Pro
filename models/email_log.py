"""
Modelo para registrar el historial de envíos de notificaciones por email
"""
from .database import db
from datetime import datetime


class EmailNotificationLog(db.Model):
    """Registro de cada notificación enviada por email"""
    __tablename__ = "email_notification_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)  # 'entry' o 'exit'
    email_to = db.Column(db.String(120), nullable=False)
    additional_email_to = db.Column(db.String(120), nullable=True)
    scheduled_time = db.Column(db.Time, nullable=False)  # Hora configurada
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.Text, nullable=True)

    # Relación con User
    user = db.relationship("User", backref="email_logs", lazy=True)

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<EmailLog {status} {self.notification_type} to {self.email_to} at {self.sent_at}>"
