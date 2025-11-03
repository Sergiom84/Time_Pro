"""
Script de diagnóstico para verificar las notificaciones por email
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, db, mail
from models.models import User

def check_notification_settings():
    """Verifica la configuración de notificaciones del usuario"""
    with app.app_context():
        # Buscar usuario Emcentro2
        user = User.query.filter_by(username='Emcentro2').first()

        if not user:
            print("Usuario 'Emcentro2' no encontrado")
            return

        print("=" * 60)
        print(f"Usuario: {user.username}")
        print(f"Email principal: {user.email}")
        print(f"Email adicional: {user.additional_notification_email or 'No configurado'}")
        print(f"Notificaciones activas: {user.email_notifications}")
        print(f"Dias seleccionados: {user.notification_days}")
        print(f"Hora de entrada: {user.notification_time_entry}")
        print(f"Hora de salida: {user.notification_time_exit}")
        print("=" * 60)

        # Verificar si hoy es un día válido
        now = datetime.now()
        current_weekday = now.weekday()
        weekday_map = {0: 'L', 1: 'M', 2: 'X', 3: 'J', 4: 'V', 5: 'S', 6: 'D'}
        today_letter = weekday_map.get(current_weekday)

        print(f"\nHoy es: {now.strftime('%A, %d/%m/%Y %H:%M:%S')}")
        print(f"Letra del día: {today_letter}")

        if user.notification_days:
            selected_days = [day.strip() for day in user.notification_days.split(',')]
            print(f"Días configurados: {selected_days}")
            print(f"¿Hoy está incluido?: {today_letter in selected_days}")

        # Calcular diferencia de tiempo con la hora de salida
        if user.notification_time_exit:
            current_time = now.time()
            time_diff = (datetime.combine(datetime.today(), current_time) -
                        datetime.combine(datetime.today(), user.notification_time_exit)).total_seconds() / 60

            print(f"\nHora actual: {current_time.strftime('%H:%M:%S')}")
            print(f"Hora de salida configurada: {user.notification_time_exit.strftime('%H:%M:%S')}")
            print(f"Diferencia en minutos: {time_diff:.2f}")
            print(f"¿Está en ventana de envío (-5 a 0 min)?: {-5 <= time_diff <= 0}")

        # Verificar configuración de email
        print("\n" + "=" * 60)
        print("CONFIGURACION DE EMAIL:")
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        print(f"MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', ''))}")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        print("=" * 60)

def test_send_email():
    """Prueba de envío de email manual"""
    with app.app_context():
        from tasks.email_service import send_notification_email

        user = User.query.filter_by(username='Emcentro2').first()

        if not user:
            print("Usuario 'Emcentro2' no encontrado")
            return

        print("\nIntentando enviar email de prueba...")
        result = send_notification_email(mail, user, 'exit')

        if result:
            print("✓ Email enviado exitosamente")
        else:
            print("✗ Error al enviar email")

if __name__ == "__main__":
    print("\n1. Verificando configuración de notificaciones...")
    check_notification_settings()

    print("\n\n2. ¿Quieres enviar un email de prueba? (s/n): ", end='')
    response = input().strip().lower()

    if response == 's':
        test_send_email()
