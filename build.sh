#!/bin/bash
# Build script for Render - ejecutar migraciones de Flask
set -e

echo "==== Building Time Pro ===="
echo "Migrating database..."

# Aseguramos que Flask sepa qué app cargar
export FLASK_APP=main.py

# Ejecutar migraciones de Alembic/Flask-Migrate
flask db upgrade

echo "==== Build completed successfully ===="
