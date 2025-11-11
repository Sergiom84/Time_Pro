#!/bin/bash
# Script para verificar el estado de Time Pro

echo "🔍 Verificando estado de Time Pro..."
echo ""

# Buscar procesos Python relacionados con main.py
PIDS=$(pgrep -f "python.*main.py")

if [ -n "$PIDS" ]; then
    echo "✅ Instancias activas:"
    ps aux | grep "python.*main.py" | grep -v grep | awk '{printf "  📌 PID: %s | Usuario: %s | CPU: %s%% | Mem: %s%%\n", $2, $1, $3, $4}'
else
    echo "⭕ No hay instancias de Time Pro corriendo"
fi

echo ""
echo "Comandos disponibles:"
echo "  bash run_pro.sh     - Iniciar versión Pro"
echo "  bash run_lite.sh    - Iniciar versión Lite"
echo "  bash stop_app.sh    - Detener todas las instancias"
