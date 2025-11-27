#!/bin/bash

# Script para configurar el cliente "Patacones de mi tierra"

echo "=================================================================="
echo "  CONFIGURACIÓN DEL CLIENTE: PATACONES DE MI TIERRA (LITE)"
echo "=================================================================="
echo ""

# Verificar que exista el archivo .env
if [ ! -f ".env" ]; then
    echo "❌ Error: Archivo .env no encontrado."
    echo "   Por favor, asegúrate de que el archivo .env existe con la configuración de Supabase."
    exit 1
fi

echo "✓ Archivo .env encontrado"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado."
    exit 1
fi

echo "✓ Python $(python3 --version) encontrado"
echo ""

# Verificar/instalar dependencias
echo "📦 Verificando dependencias de Python..."

# Intentar importar las bibliotecas necesarias
python3 -c "
import sys
try:
    import flask
    import flask_sqlalchemy
    import werkzeug
    import psycopg2
    import dotenv
    print('✓ Todas las dependencias están instaladas')
    sys.exit(0)
except ImportError as e:
    print(f'⚠️  Falta dependencia: {e}')
    print('')
    print('📥 Instalando dependencias necesarias...')
    sys.exit(1)
"

# Si faltan dependencias, intentar instalarlas
if [ $? -ne 0 ]; then
    echo ""
    echo "Opciones para instalar dependencias:"
    echo "1. Con pip install --user:"
    echo "   python3 -m pip install --user Flask Flask-SQLAlchemy psycopg2-binary python-dotenv werkzeug sqlalchemy"
    echo ""
    echo "2. Con --break-system-packages (Ubuntu 23.04+):"
    echo "   python3 -m pip install --break-system-packages Flask Flask-SQLAlchemy psycopg2-binary python-dotenv werkzeug sqlalchemy"
    echo ""
    echo "3. Desde requirements.txt:"
    echo "   python3 -m pip install --user -r requirements.txt"
    echo ""
    read -p "¿Deseas intentar instalar automáticamente con --user? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        python3 -m pip install --user Flask Flask-SQLAlchemy psycopg2-binary python-dotenv werkzeug sqlalchemy
        if [ $? -ne 0 ]; then
            echo "❌ Error al instalar dependencias. Por favor, instálalas manualmente."
            exit 1
        fi
    else
        echo "Por favor, instala las dependencias manualmente y vuelve a ejecutar este script."
        exit 1
    fi
fi

echo ""
echo "=================================================================="
echo "  EJECUTANDO SCRIPT DE CONFIGURACIÓN"
echo "=================================================================="
echo ""

# Ejecutar el script de configuración
python3 create_patacones_client.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================================="
    echo "  ✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE"
    echo "=================================================================="
    echo ""
    echo "El cliente 'Patacones de mi tierra' ha sido creado."
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Inicia la aplicación: python3 main.py"
    echo "2. Accede en tu navegador: http://localhost:5000"
    echo "3. Inicia sesión con las credenciales mostradas arriba"
    echo "4. Crea empleados desde el panel de administración"
    echo ""
else
    echo ""
    echo "❌ Hubo un error durante la configuración."
    echo "   Por favor, revisa los mensajes de error arriba."
    echo ""
    echo "Alternativas:"
    echo "1. Ejecuta manualmente: python3 create_patacones_client.py"
    echo "2. Usa el script interactivo: python3 scripts/setup_client.py"
    echo "3. Sigue las instrucciones en SETUP_PATACONES.md"
    echo ""
fi
