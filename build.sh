#!/bin/bash
# Build script for Render - instalar dependencias y ejecutar migraciones
set -e

echo "==== Building Time Pro ===="
echo "Installing dependencies..."

# Instalar dependencias desde requirements.txt
pip install -r requirements.txt

echo "Migrating database..."

# Aseguramos que Flask sepa qué app cargar
export FLASK_APP=main.py

# Ejecutar migraciones de Alembic/Flask-Migrate
flask db upgrade

echo "==== Build completed successfully ===="
