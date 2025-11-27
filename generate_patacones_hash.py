#!/usr/bin/env python3
"""Genera el hash de contraseña para el administrador de Patacones"""
from werkzeug.security import generate_password_hash

password = "Patacones2025!"
hash_value = generate_password_hash(password)

print(f"Contraseña: {password}")
print(f"Hash: {hash_value}")
print()
print("Copia este hash y úsalo en el archivo setup_patacones.sql")
