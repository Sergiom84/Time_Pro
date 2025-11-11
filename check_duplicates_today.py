"""
Verificar duplicados en los logs de hoy
"""
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from urllib.parse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

uri = os.getenv("DATABASE_URL")
if uri:
    uri = uri.replace("postgres://", "postgresql://")
else:
    # Desarrollo local: SQLite por defecto (no exponer secretos)
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    uri = f"sqlite:///{os.path.join(instance_dir, 'app.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models.database import db
db.init_app(app)

from models.models import User
from models.email_log import EmailNotificationLog

with app.app_context():
    print("\n" + "=" * 80)
    print("📧 VERIFICACIÓN DE DUPLICADOS - HOY")
    print("=" * 80)

    today = datetime.now().date()

    # Obtener logs de hoy
    logs_today = EmailNotificationLog.query.filter(
        db.func.date(EmailNotificationLog.sent_at) == today
    ).order_by(EmailNotificationLog.sent_at.desc()).all()

    if not logs_today:
        print("\n❌ No hay logs de hoy")
    else:
        print(f"\n✓ Total de envíos hoy: {len(logs_today)}\n")

        # Agrupar por usuario y tipo
        user_logs = {}
        for log in logs_today:
            key = (log.user_id, log.notification_type)
            if key not in user_logs:
                user_logs[key] = []
            user_logs[key].append(log)

        # Mostrar resultados
        duplicates_found = False
        for (user_id, notif_type), logs in user_logs.items():
            user = User.query.get(user_id)
            type_name = "ENTRADA" if notif_type == "entry" else "SALIDA"

            print(f"👤 {user.full_name} ({user.username}) - {type_name}")
            print(f"   Envíos: {len(logs)}")

            for i, log in enumerate(logs, 1):
                status = "✓" if log.success else "✗"
                print(f"   {i}. {status} {log.sent_at.strftime('%H:%M:%S')} → {log.email_to}")

            if len(logs) > 1:
                print(f"   ⚠️  DUPLICADO DETECTADO: {len(logs)} envíos del mismo tipo")
                duplicates_found = True

                # Calcular diferencia de tiempo entre envíos
                if len(logs) >= 2:
                    time_diff = (logs[0].sent_at - logs[1].sent_at).total_seconds()
                    print(f"   ⏱️  Diferencia: {abs(time_diff):.1f} segundos")
            else:
                print(f"   ✅ Sin duplicados")

            print()

        print("=" * 80)
        if duplicates_found:
            print("❌ SE DETECTARON DUPLICADOS")
            print("\nCAUSA: Múltiples workers/procesos ejecutando el scheduler simultáneamente")
            print("\nSOLUCIÓN IMPLEMENTADA:")
            print("  ✓ Versión V3 con lock distribuido (PostgreSQL advisory lock)")
            print("  ✓ Solo un proceso podrá ejecutar el scheduler a la vez")
            print("  ✓ Los demás procesos saldrán inmediatamente si ya hay uno ejecutando")
            print("\n⚠️  IMPORTANTE: Reinicia la aplicación para usar V3")
        else:
            print("✅ NO SE DETECTARON DUPLICADOS")
        print("=" * 80 + "\n")
