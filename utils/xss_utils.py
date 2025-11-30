"""
Utilidades para prevenir ataques XSS (Cross-Site Scripting)
Sanitiza entradas de usuario removiendo scripts y código malicioso
"""

import bleach

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
