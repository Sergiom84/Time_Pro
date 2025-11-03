"""
Script para probar el envío de email directamente
"""
import os
import sys
from flask_mail import Mail, Message
from flask import Flask

# Crear app básica
app = Flask(__name__)

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'sergio.hlara84@gmail.com'
app.config['MAIL_PASSWORD'] = 'mrgl uqhm cuhe rerw'
app.config['MAIL_DEFAULT_SENDER'] = 'sergio.hlara84@gmail.com'

mail = Mail(app)

def send_test_email():
    """Envía un email de prueba"""
    try:
        with app.app_context():
            msg = Message(
                subject='⏰ TEST - Recordatorio de Fichaje de Salida',
                recipients=['sergiohernandezlara07@gmail.com'],
                body="""
Hola,

Este es un email de PRUEBA del sistema de notificaciones de Time Tracker.

Si recibes este correo, significa que el envío de emails funciona correctamente.

El problema podría estar en el scheduler (APScheduler) que no se está ejecutando cada 5 minutos.

---
Time Tracker - Sistema de Control de Fichajes
                """
            )

            print("Enviando email de prueba...")
            mail.send(msg)
            print("OK - Email enviado exitosamente a: sergiohernandezlara07@gmail.com")
            print("Revisa tu bandeja de entrada (o spam)")
            return True

    except Exception as e:
        print(f"ERROR - Al enviar email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_test_email()
