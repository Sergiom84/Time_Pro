# Importar todos los modelos para que Flask-Migrate los detecte
from .models import User, TimeRecord, EmployeeStatus, WorkPause, LeaveRequest, SystemConfig
from .email_log import EmailNotificationLog

__all__ = ['User', 'TimeRecord', 'EmployeeStatus', 'WorkPause', 'LeaveRequest', 'SystemConfig', 'EmailNotificationLog']
