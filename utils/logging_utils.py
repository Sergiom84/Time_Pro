from urllib.parse import urlparse
import logging


def mask_dsn(dsn: str) -> str:
    """
    Enmascara la contraseña de una cadena DSN para evitar
    que aparezca en logs o mensajes de depuración.
    """
    try:
        parsed = urlparse(dsn)
        if parsed.password:
            return dsn.replace(parsed.password, "****")
        return dsn
    except Exception:
        return dsn


def get_logger(name=None):
    """
    Obtiene logger configurado para la app Flask.

    Si se ejecuta dentro de un app context (peticiones Flask),
    retorna current_app.logger.

    Si no hay app context (scripts/CLI), retorna un logger estándar.

    Args:
        name: Nombre del logger (usado si no hay app context)

    Returns:
        Logger configurado para la aplicación
    """
    try:
        from flask import current_app
        return current_app.logger
    except RuntimeError:
        # No hay app context (se ejecuta desde script/CLI)
        return logging.getLogger(name or __name__)


def log_exception(exc, context=""):
    """
    Helper para loguear excepciones con contexto.
    Loguea la excepción completa con traceback.

    Args:
        exc: La excepción a loguear
        context: Contexto adicional (ej: "Error en check_in")
    """
    logger = get_logger()
    message = f"{context}: {str(exc)}" if context else str(exc)
    logger.error(message, exc_info=True)

