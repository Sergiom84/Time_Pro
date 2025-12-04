"""
Utilidades para manejo de zonas horarias.
La aplicación usa zona horaria de España (CET/CEST).
"""
from datetime import datetime
from pytz import timezone

# Zona horaria de España
SPAIN_TZ = timezone('Europe/Madrid')


def get_now_spain():
    """
    Obtiene la hora actual en zona horaria de España (CET/CEST).
    
    Returns:
        datetime: Hora actual en zona horaria de España (sin información de zona)
    
    Ejemplo:
        >>> now = get_now_spain()
        >>> print(now)  # 2025-12-04 10:30:45.123456
    """
    # Obtener hora UTC actual
    utc_now = datetime.utcnow()
    
    # Convertir a zona horaria de España
    utc_aware = timezone('UTC').localize(utc_now)
    spain_time = utc_aware.astimezone(SPAIN_TZ)
    
    # Retornar sin información de zona (naive datetime)
    # para compatibilidad con SQLAlchemy
    return spain_time.replace(tzinfo=None)


def get_now_spain_aware():
    """
    Obtiene la hora actual en zona horaria de España (con información de zona).
    
    Returns:
        datetime: Hora actual en zona horaria de España (aware)
    """
    utc_now = datetime.utcnow()
    utc_aware = timezone('UTC').localize(utc_now)
    return utc_aware.astimezone(SPAIN_TZ)

