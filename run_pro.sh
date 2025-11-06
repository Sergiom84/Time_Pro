#!/bin/bash
# Script para arrancar versión Pro limpiamente

echo "🛑 Deteniendo instancias anteriores..."
pkill -9 -f "python.*main.py" 2>/dev/null
sleep 2

echo "🚀 Iniciando Time Pro..."
export APP_PLAN=pro

# Usar python3 o python del venv si está activado
if [ -n "$VIRTUAL_ENV" ]; then
    python main.py
else
    python3 main.py
fi
