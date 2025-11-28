#!/usr/bin/env python3
"""
Script para importar empleados masivamente desde archivo CSV o Excel.

Formato CSV esperado:
username,password,full_name,email,weekly_hours,center_name,category_name
juan.perez,pass123,Juan Pérez,juan@ejemplo.com,40,Centro 1,Empleado
maria.gomez,pass456,María Gómez,maria@ejemplo.com,30,Centro 2,Coordinador

Uso: python import_employees_csv.py
"""
import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from models.database import db
from models.models import Client, User, Center, Category
from main import app

# Intentar importar pandas para soporte Excel (opcional)
try:
    import pandas as pd
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


def select_client():
    """Permite al usuario seleccionar un cliente"""
    with app.app_context():
        clients = Client.query.order_by(Client.name).all()

        if not clients:
            print("❌ No hay clientes en la base de datos")
            print("   Ejecuta primero: python create_client.py")
            return None

        print()
        print("CLIENTES DISPONIBLES:")
        print("-" * 70)
        for idx, client in enumerate(clients, 1):
            user_count = User.query.filter_by(client_id=client.id).count()
            print(f"{idx}. {client.name} ({client.plan.upper()}) - {user_count} usuarios")
        print()

        while True:
            try:
                selection = input(f"Selecciona un cliente (1-{len(clients)}): ").strip()
                idx = int(selection) - 1
                if 0 <= idx < len(clients):
                    return clients[idx]
                print(f"❌ Número inválido. Debe estar entre 1 y {len(clients)}")
            except ValueError:
                print("❌ Debe ser un número")


def leer_archivo(archivo_path):
    """
    Lee CSV o Excel y retorna lista de diccionarios.

    Args:
        archivo_path: Ruta al archivo CSV o Excel

    Returns:
        list[dict]: Cada dict es una fila del archivo
    """
    ext = Path(archivo_path).suffix.lower()

    if ext in ['.xlsx', '.xls']:
        if not EXCEL_SUPPORT:
            raise ValueError(
                "Para importar archivos Excel, instala pandas:\n"
                "  pip install pandas openpyxl"
            )
        df = pd.read_excel(archivo_path)
        # Convertir NaN a cadenas vacías
        df = df.fillna('')
        return df.to_dict('records')

    elif ext == '.csv':
        with open(archivo_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    else:
        raise ValueError(
            f"Formato no soportado: {ext}\n"
            f"Usa archivos .csv, .xlsx o .xls"
        )


def validar_fila(fila, num_fila, client_id, usernames_existentes, emails_existentes):
    """
    Valida una fila del archivo.

    Args:
        fila: Diccionario con datos de la fila
        num_fila: Número de fila (para mensajes)
        client_id: ID del cliente
        usernames_existentes: Set de usernames ya en BD o CSV
        emails_existentes: Set de emails ya en BD o CSV

    Returns:
        tuple: (es_valida: bool, errores: list[str])
    """
    errores = []

    # Campos obligatorios
    if not fila.get('username', '').strip():
        errores.append(f"Fila {num_fila}: Username obligatorio")

    if not fila.get('password', '').strip():
        errores.append(f"Fila {num_fila}: Password obligatorio")

    if not fila.get('full_name', '').strip():
        errores.append(f"Fila {num_fila}: Nombre completo (full_name) obligatorio")

    if not fila.get('email', '').strip():
        errores.append(f"Fila {num_fila}: Email obligatorio")

    # Unicidad username
    username = fila.get('username', '').strip()
    if username and username in usernames_existentes:
        errores.append(f"Fila {num_fila}: Username '{username}' duplicado")

    # Unicidad email
    email = fila.get('email', '').strip()
    if email and email in emails_existentes:
        errores.append(f"Fila {num_fila}: Email '{email}' duplicado")

    # Validar centro existe (si especificado)
    center_name = fila.get('center_name', '').strip()
    if center_name:
        center = Center.query.filter_by(
            client_id=client_id,
            name=center_name
        ).first()
        if not center:
            errores.append(f"Fila {num_fila}: Centro '{center_name}' no existe")

    # Validar categoría existe (si especificada)
    category_name = fila.get('category_name', '').strip()
    if category_name:
        category = Category.query.filter_by(
            client_id=client_id,
            name=category_name
        ).first()
        if not category:
            errores.append(f"Fila {num_fila}: Categoría '{category_name}' no existe")

    # Validar weekly_hours es número (si especificado)
    weekly_hours = fila.get('weekly_hours', '').strip()
    if weekly_hours:
        try:
            int(weekly_hours)
        except ValueError:
            errores.append(f"Fila {num_fila}: weekly_hours debe ser un número entero")

    return (len(errores) == 0, errores)


def importar_empleados(client, datos_csv):
    """
    Importa empleados desde lista de diccionarios.

    Args:
        client: Objeto Client
        datos_csv: Lista de diccionarios con datos de empleados

    Returns:
        dict: Resumen de importación
    """
    with app.app_context():
        # 1. VALIDAR LÍMITES DE PLAN
        usuarios_actuales = User.query.filter_by(client_id=client.id).count()
        usuarios_a_importar = len(datos_csv)

        if client.plan == 'lite':
            if usuarios_actuales + usuarios_a_importar > 5:
                return {
                    'exito': False,
                    'errores': [
                        f"Plan Lite permite máximo 5 usuarios.",
                        f"Usuarios actuales: {usuarios_actuales}",
                        f"Usuarios a importar: {usuarios_a_importar}",
                        f"Total: {usuarios_actuales + usuarios_a_importar}",
                        f"Para importar estos empleados, actualiza el plan a PRO."
                    ],
                    'importados': 0
                }

        # 2. OBTENER USERNAMES Y EMAILS EXISTENTES
        usernames_existentes = set(
            u.username for u in User.query.filter_by(client_id=client.id).all()
        )
        emails_existentes = set(
            u.email for u in User.query.filter_by(client_id=client.id).all()
        )

        # 3. VALIDAR TODAS LAS FILAS (DRY-RUN)
        errores_validacion = []
        usernames_csv = set()
        emails_csv = set()

        for i, fila in enumerate(datos_csv, start=1):
            # Validar
            es_valida, errores = validar_fila(
                fila, i, client.id,
                usernames_existentes | usernames_csv,
                emails_existentes | emails_csv
            )

            if not es_valida:
                errores_validacion.extend(errores)
            else:
                # Añadir a sets para detectar duplicados en CSV
                username = fila.get('username', '').strip()
                email = fila.get('email', '').strip()
                if username:
                    usernames_csv.add(username)
                if email:
                    emails_csv.add(email)

        # Si hay errores, abortar
        if errores_validacion:
            return {
                'exito': False,
                'errores': errores_validacion,
                'importados': 0
            }

        # 4. IMPORTAR (TODO O NADA)
        empleados_creados = []

        try:
            for fila in datos_csv:
                # Buscar centro
                center_id = None
                center_name = fila.get('center_name', '').strip()
                if center_name:
                    center = Center.query.filter_by(
                        client_id=client.id,
                        name=center_name
                    ).first()
                    center_id = center.id if center else None

                # Buscar categoría
                category_id = None
                category_name = fila.get('category_name', '').strip()
                if category_name:
                    category = Category.query.filter_by(
                        client_id=client.id,
                        name=category_name
                    ).first()
                    category_id = category.id if category else None

                # Crear empleado
                empleado = User(
                    client_id=client.id,
                    username=fila['username'].strip(),
                    full_name=fila['full_name'].strip(),
                    email=fila['email'].strip(),
                    role=None,  # Empleado normal (no admin)
                    is_active=True,
                    weekly_hours=int(fila.get('weekly_hours', '40') or 40),
                    center_id=center_id,
                    category_id=category_id,
                    theme_preference='dark-turquoise'
                )

                empleado.set_password(fila['password'].strip())

                db.session.add(empleado)
                empleados_creados.append({
                    'username': empleado.username,
                    'full_name': empleado.full_name,
                    'email': empleado.email
                })

            # Commit todo junto (transacción atómica)
            db.session.commit()

            return {
                'exito': True,
                'importados': len(empleados_creados),
                'detalles': empleados_creados
            }

        except Exception as e:
            db.session.rollback()
            import traceback
            return {
                'exito': False,
                'errores': [
                    f"Error al importar: {str(e)}",
                    "Detalles:",
                    traceback.format_exc()
                ],
                'importados': 0
            }


def main():
    print("=" * 70)
    print("        TIME PRO - IMPORTAR EMPLEADOS DESDE CSV/EXCEL")
    print("=" * 70)
    print()

    # Mostrar información sobre soporte Excel
    if not EXCEL_SUPPORT:
        print("ℹ️  Soporte Excel no disponible.")
        print("   Para importar archivos Excel (.xlsx, .xls), instala pandas:")
        print("   pip install pandas openpyxl")
        print()
        print("   Archivos CSV (.csv) funcionan sin instalación adicional.")
        print()

    # 1. Seleccionar cliente
    print("PASO 1: SELECCIONAR CLIENTE")
    print("-" * 70)
    client = select_client()

    if not client:
        return 1

    print()
    print(f"✅ Cliente seleccionado: {client.name} ({client.plan.upper()})")
    print()

    # 2. Solicitar archivo
    print("PASO 2: SELECCIONAR ARCHIVO")
    print("-" * 70)
    print("Formato CSV esperado:")
    print("  username,password,full_name,email,weekly_hours,center_name,category_name")
    print()
    archivo_path = input("Ruta del archivo CSV/Excel: ").strip()

    if not Path(archivo_path).exists():
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return 1

    # 3. Leer archivo
    print()
    print("PASO 3: LEER ARCHIVO")
    print("-" * 70)
    print(f"📂 Leyendo archivo...")
    try:
        datos_csv = leer_archivo(archivo_path)
        if not datos_csv:
            print("❌ El archivo está vacío")
            return 1
        print(f"✅ {len(datos_csv)} filas encontradas")
    except Exception as e:
        print(f"❌ Error al leer archivo: {e}")
        return 1

    # 4. Preview
    print()
    print("PASO 4: PREVIEW")
    print("=" * 70)
    print(f"Cliente: {client.name}")
    print(f"Plan: {client.plan.upper()}")
    print(f"Empleados actuales: {User.query.filter_by(client_id=client.id).count()}")
    print(f"Empleados a importar: {len(datos_csv)}")
    print()
    print("Primeros empleados:")
    print("-" * 70)

    for i, fila in enumerate(datos_csv[:5], start=1):  # Mostrar primeros 5
        print(f"{i}. {fila.get('username', 'N/A'):20s} - {fila.get('full_name', 'N/A')}")

    if len(datos_csv) > 5:
        print(f"... y {len(datos_csv) - 5} más")

    print()

    # 5. Confirmar
    confirmar = input("¿Proceder con la importación? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Importación cancelada")
        return 1

    # 6. Importar
    print()
    print("PASO 5: IMPORTAR")
    print("-" * 70)
    print("📝 Validando e importando empleados...")
    print()

    resultado = importar_empleados(client, datos_csv)

    # 7. Mostrar resultado
    print()
    print("=" * 70)
    if resultado['exito']:
        print("✅ IMPORTACIÓN EXITOSA")
        print("=" * 70)
        print(f"Empleados importados: {resultado['importados']}")
        print()
        print("Empleados creados:")
        for emp in resultado['detalles']:
            print(f"  • {emp['username']:20s} - {emp['full_name']}")
    else:
        print("❌ IMPORTACIÓN FALLIDA")
        print("=" * 70)
        print("Errores encontrados:")
        for error in resultado['errores']:
            print(f"  • {error}")

    print()
    print("=" * 70)
    print()

    return 0 if resultado['exito'] else 1


if __name__ == "__main__":
    sys.exit(main())
