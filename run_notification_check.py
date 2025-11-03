"""
Script para ejecutar manualmente el chequeo de notificaciones
Útil para debugging
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, mail
from tasks.email_service import check_and_send_notifications

if __name__ == "__main__":
    print("=" * 70)
    print("EJECUCIÓN MANUAL DEL CHEQUEO DE NOTIFICACIONES")
    print("=" * 70)

    check_and_send_notifications(app, mail)

    print("\n" + "=" * 70)
    print("Chequeo completado. Revisa los logs arriba.")
    print("=" * 70)
