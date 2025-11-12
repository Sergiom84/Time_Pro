#!/usr/bin/env python3
"""
Script simple para generar hash de contraseña para Supabase
Uso: python generate_password_hash.py
"""
from werkzeug.security import generate_password_hash

print("=" * 60)
print("    GENERADOR DE HASH DE CONTRASEÑA")
print("=" * 60)
print()
print("Este script genera el hash de una contraseña para insertarla")
print("manualmente en Supabase.")
print()

password = input("Introduce la contraseña: ").strip()

if not password:
    print("❌ La contraseña no puede estar vacía")
    exit(1)

print("\n🔐 Generando hash...")
password_hash = generate_password_hash(password)

print("\n" + "=" * 60)
print("    ✅ HASH GENERADO")
print("=" * 60)
print()
print("Copia este hash y pégalo en el campo 'password_hash' de Supabase:")
print()
print(password_hash)
print()
print("=" * 60)
print("\n💡 CÓMO USAR EN SUPABASE:")
print("   1. Ve a la tabla 'user' en Supabase")
print("   2. Click 'Insert' → 'Insert row'")
print("   3. Completa los campos:")
print("      - client_id: 4")
print("      - username: tu_usuario")
print("      - password_hash: [PEGA EL HASH DE ARRIBA]")
print("      - full_name: Tu Nombre")
print("      - email: tu@email.com")
print("      - is_admin: true")
print("      - is_active: true")
print("      - weekly_hours: 40")
print("      - centro: -- Sin categoría --")
print("      - categoria: Gestor")
print("      - theme_preference: dark-turquoise")
print("   4. Click 'Save'")
print("=" * 60)
