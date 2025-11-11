#!/usr/bin/env python3
"""
Script para verificar que el aislamiento multi-tenant funciona correctamente.
"""
from main import app
from models.database import db
from models.models import User, TimeRecord, Client
from flask import session

print("="*60)
print("TEST DE AISLAMIENTO MULTI-TENANT")
print("="*60)

with app.app_context():
    # Verificar que existe el cliente por defecto
    print("\n1. Verificando cliente por defecto...")
    client = Client.query.filter_by(id=1).first()
    if client:
        print(f"   [OK] Cliente encontrado: {client.name} (plan: {client.plan})")
    else:
        print("   [ERROR] No se encontró el cliente por defecto")

    # Verificar que todos los usuarios tienen client_id
    print("\n2. Verificando usuarios con client_id...")
    users_without_client = User.query.filter(User.client_id.is_(None)).count()
    total_users = User.query.count()
    if users_without_client == 0:
        print(f"   [OK] Todos los {total_users} usuarios tienen client_id asignado")
    else:
        print(f"   [ERROR] {users_without_client} usuarios sin client_id")

    # Verificar que todos los registros tienen client_id
    print("\n3. Verificando TimeRecords con client_id...")
    records_without_client = TimeRecord.query.filter(TimeRecord.client_id.is_(None)).count()
    total_records = TimeRecord.query.count()
    if records_without_client == 0:
        print(f"   [OK] Todos los {total_records} registros tienen client_id asignado")
    else:
        print(f"   [ERROR] {records_without_client} registros sin client_id")

    # Simular sesión con client_id para probar filtrado automático
    print("\n4. Probando filtrado automático con sesión...")
    with app.test_request_context():
        # Simular login con client_id = 1
        session['client_id'] = 1

        # Intentar query que debería ser filtrado automáticamente
        from utils.multitenant import get_current_client_id
        print(f"   Client ID en sesión: {get_current_client_id()}")

        # Query de usuarios (debería ser filtrado automáticamente)
        users = User.query.all()
        print(f"   Usuarios encontrados: {len(users)}")

        # Verificar que todos tienen el mismo client_id
        unique_clients = set(u.client_id for u in users)
        if unique_clients == {1}:
            print(f"   [OK] Todos los usuarios pertenecen al cliente 1")
        else:
            print(f"   [WARNING] Se encontraron usuarios de múltiples clientes: {unique_clients}")

    print("\n" + "="*60)
    print("[INFO] Prueba de aislamiento completada")
    print("="*60)
    print("\n[NOTA] El filtrado automático solo funciona durante peticiones HTTP reales,")
    print("       no en scripts standalone. Para probar completamente, usa la app web.")
