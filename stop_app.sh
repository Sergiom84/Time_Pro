#!/bin/bash
# Script para detener todas las instancias de la app

echo "🛑 Deteniendo todas las instancias de Time Pro..."

# Buscar procesos Python relacionados con main.py
PIDS=$(pgrep -f "python.*main.py")

if [ -z "$PIDS" ]; then
    echo "✅ No hay instancias corriendo"
else
    echo "📋 Procesos encontrados: $PIDS"
    pkill -9 -f "python.*main.py"
    sleep 1
    echo "✅ Instancias detenidas"
fi

# Verificar
REMAINING=$(pgrep -f "python.*main.py")
if [ -z "$REMAINING" ]; then
    echo "✅ Todas las instancias cerradas correctamente"
else
    echo "⚠️ Aún quedan procesos activos:"
    ps aux | grep "python.*main.py" | grep -v grep
fi
