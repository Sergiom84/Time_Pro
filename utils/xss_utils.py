"""
Utilidades para prevenir ataques XSS (Cross-Site Scripting)
Sanitiza entradas de usuario removiendo scripts y código malicioso
"""

import bleach
import re

# Tags HTML permitidos (vacío = no permite HTML)
ALLOWED_TAGS = []

# Atributos permitidos (vacío = no permite atributos)
ALLOWED_ATTRIBUTES = {}


def sanitize_text(text):
    """
    Sanitiza texto removiendo cualquier contenido HTML/JavaScript.
    Seguro para campos de texto libre como notas, razones, etc.

    Args:
        text: String a sanitizar

    Returns:
        String sanitizado sin scripts ni HTML
    """
    if not text:
        return ""

    if not isinstance(text, str):
        return str(text)

    # Bleach limpia cualquier HTML/JS, dejando solo texto plano
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def sanitize_input(data):
    """
    Sanitiza un diccionario completo de datos de formulario.
    Útil para procesar múltiples campos a la vez.

    Args:
        data: Dict con datos del formulario

    Returns:
        Dict con datos sanitizados
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        else:
            sanitized[key] = value

    return sanitized


def sanitize_username(username):
    """
    Limpia y valida username (alfanumérico + guiones, puntos, guiones bajos).

    IMPORTANTE: SOLO usar en REGISTRO de nuevos usuarios, NO en login.
    En login, usar .strip() para no transformar credenciales existentes.

    Args:
        username: String a sanitizar

    Returns:
        Username limpio con longitud limitada a 80 caracteres
    """
    if not username:
        return ""

    # Strip primero
    username = username.strip()

    # Remover caracteres peligrosos (permite guiones, puntos, guiones bajos)
    # Pattern: word chars (\w = alfanuméricos + _) + guiones + puntos
    clean = re.sub(r'[^\w\-.]', '', username)

    return clean[:80]  # Límite de longitud


def sanitize_name(name):
    """
    Limpia nombres de personas (permite espacios, acentos, guiones).

    IMPORTANTE: SOLO usar en REGISTRO o formularios de datos personales.
    Los nombres con caracteres especiales ya existentes en BD no deben romperse.

    Args:
        name: String a sanitizar

    Returns:
        Nombre limpio con longitud limitada a 100 caracteres
    """
    if not name:
        return ""

    # Strip primero
    name = name.strip()

    # Permite letras (con acentos), espacios, guiones
    # [\w\-] = alfanuméricos + guiones, más explícitamente permitimos acentos
    clean = re.sub(r'[^\w\s\-áéíóúñÁÉÍÓÚÑ]', '', name)

    return clean.strip()[:100]  # Strip después también, limitar longitud


def validate_email(email):
    """
    Valida formato de email usando expresión regular.

    Args:
        email: String a validar

    Returns:
        True si el email tiene formato válido, False en caso contrario
    """
    if not email:
        return False

    email = email.strip()

    # Patrón de validación de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    return bool(re.match(pattern, email))
