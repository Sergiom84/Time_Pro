"""
Test para verificar que el remitente aparece como "TimeTracker" sin mostrar el email
"""
import sys
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mail import Mail, Message
from urllib.parse import quote_plus

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configurar Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))

mail = Mail(app)

print("\n" + "=" * 80)
print("📧 TEST DE NOMBRE DE REMITENTE")
print("=" * 80)

print(f"\nConfiguración actual:")
print(f"  MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"  MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")

if '<' in app.config['MAIL_DEFAULT_SENDER']:
    print(f"\n✅ Configurado con nombre personalizado")
    print(f"   El remitente se verá como: {app.config['MAIL_DEFAULT_SENDER'].split('<')[0].strip()}")
else:
    print(f"\n⚠️  Solo configurado con email")
    print(f"   El remitente se verá como: {app.config['MAIL_DEFAULT_SENDER']}")

confirm = input("\n¿Enviar correo de prueba a sergiohernandezlara07@gmail.com? (s/n): ").strip().lower()
if confirm != 's':
    print("Cancelado")
    sys.exit(0)

with app.app_context():
    try:
        msg = Message(
            subject="✅ Prueba de Remitente - TimeTracker",
            recipients=["sergiohernandezlara07@gmail.com"],
            body="""
Hola,

Este es un correo de prueba para verificar que el remitente aparece correctamente.

Si ves este correo, verifica en tu cliente de correo:
- ¿El remitente dice "TimeTracker"?
- ¿O dice "sergio.hlara84@gmail.com"?

Si aparece solo "TimeTracker", la configuración es correcta.

---
Time Tracker - Sistema de Control de Fichajes
            """
        )

        mail.send(msg)
        print("\n✅ Correo enviado correctamente")
        print("\nVerifica en Gmail:")
        print("  1. Abre el correo")
        print("  2. Mira el campo 'De:'")
        print("  3. Debe aparecer: TimeTracker")
        print("     (sin mostrar sergio.hlara84@gmail.com)")

    except Exception as e:
        print(f"\n❌ Error al enviar: {e}")

print("\n" + "=" * 80 + "\n")
