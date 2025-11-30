"""
Funciones auxiliares reutilizables en toda la aplicación.
Centraliza lógica común para evitar duplicación.
"""


def format_timedelta(td):
    """
    Formatea un objeto timedelta en formato HH:MM.

    Args:
        td: timedelta object o None

    Returns:
        String formateado como "HH:MM" o "-" si td es None
    """
    if td is None:
        return "-"
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}"
