"""
Script para verificar las preferencias de notificación del empleado Empleado2
"""
from models.database import db
from models.models import User
from main import app

with app.app_context():
    # Buscar el usuario Empleado2
    user = User.query.filter_by(username='Empleado2').first()

    if not user:
        print("❌ Usuario 'Empleado2' no encontrado")
        print("\n📋 Usuarios disponibles:")
        all_users = User.query.all()
        for u in all_users:
            print(f"  - Username: {u.username} | Nombre: {u.full_name}")
    else:
        print("✅ Usuario encontrado:")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Nombre completo: {user.full_name}")
        print(f"   Email: {user.email}")
        print(f"   Centro: {user.centro}")
        print(f"   Categoría: {user.categoria}")

        print("\n" + "="*60)
        print("📧 PREFERENCIAS DE NOTIFICACIÓN")
        print("="*60)

        # Verificar preferencias de notificación
        print(f"   Notificaciones por email: {'✅ ACTIVADAS' if user.email_notifications else '❌ DESACTIVADAS'}")
        print(f"   Días seleccionados: {user.notification_days or '(ninguno)'}")
        print(f"   Hora de notificación entrada: {user.notification_time_entry.strftime('%H:%M') if user.notification_time_entry else '(no configurada)'}")
        print(f"   Hora de notificación salida: {user.notification_time_exit.strftime('%H:%M') if user.notification_time_exit else '(no configurada)'}")
        print(f"   Email adicional: {user.additional_notification_email or '(ninguno)'}")

        print("\n" + "="*60)
        print("💾 VALORES RAW EN LA BD")
        print("="*60)
        print(f"   email_notifications: {user.email_notifications}")
        print(f"   notification_days: {repr(user.notification_days)}")
        print(f"   notification_time_entry: {repr(user.notification_time_entry)}")
        print(f"   notification_time_exit: {repr(user.notification_time_exit)}")
        print(f"   additional_notification_email: {repr(user.additional_notification_email)}")

        # Verificar si todo está configurado correctamente
        print("\n" + "="*60)
        print("🔍 ANÁLISIS")
        print("="*60)

        if user.email_notifications:
            issues = []
            if not user.notification_days:
                issues.append("⚠️  No hay días seleccionados para las notificaciones")
            if not user.notification_time_entry and not user.notification_time_exit:
                issues.append("⚠️  No hay horarios configurados (ni entrada ni salida)")
            if not user.email:
                issues.append("❌ No hay email configurado")

            if issues:
                print("   Se encontraron los siguientes problemas:")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("   ✅ Todas las preferencias están correctamente configuradas")
                print(f"   📅 Recibirá notificaciones los días: {user.notification_days}")
                if user.notification_time_entry:
                    print(f"   🔔 Recordatorio de entrada a las: {user.notification_time_entry.strftime('%H:%M')}")
                if user.notification_time_exit:
                    print(f"   🔔 Recordatorio de salida a las: {user.notification_time_exit.strftime('%H:%M')}")
                if user.additional_notification_email:
                    print(f"   📨 Email adicional: {user.additional_notification_email}")
        else:
            print("   ℹ️  Las notificaciones por email están desactivadas")
