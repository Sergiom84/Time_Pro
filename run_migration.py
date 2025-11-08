#!/usr/bin/env python3
"""
Script para ejecutar migraciones sin flask db
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set minimal env vars needed
os.environ.setdefault('FLASK_APP', 'main.py')

try:
    from main import app, db
    from flask_migrate import upgrade

    print("Ejecutando migraciones...")
    with app.app_context():
        upgrade()
        print("✅ Migraciones ejecutadas exitosamente")
except Exception as e:
    print(f"❌ Error al ejecutar migraciones: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
