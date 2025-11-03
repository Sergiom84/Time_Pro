"""
Script de diagnóstico detallado para subida de archivos a Supabase
"""
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("TEST 1: Importar bibliotecas")
print("=" * 60)

try:
    from supabase import create_client
    print("✅ supabase importado")
    import httpx
    print(f"✅ httpx importado - versión: {httpx.__version__}")
    from storage3 import create_client as create_storage_client
    print("✅ storage3 importado")
except Exception as e:
    print(f"❌ Error importando: {e}")
    exit(1)

print("\n" + "=" * 60)
print("TEST 2: Crear cliente de Supabase")
print("=" * 60)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
print(f"KEY: {'*' * 20}...{SUPABASE_KEY[-10:] if SUPABASE_KEY else 'NO CONFIGURADA'}")

try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente creado")
except Exception as e:
    print(f"❌ Error al crear cliente: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("TEST 3: Listar buckets")
print("=" * 60)

try:
    buckets = client.storage.list_buckets()
    print(f"✅ Buckets: {[b.name for b in buckets]}")
except Exception as e:
    print(f"❌ Error al listar buckets: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("TEST 4: Subir archivo simple (sin file_options)")
print("=" * 60)

test_content = b"Contenido de prueba - test 4"
test_path = "pausas/user_999/test_simple.txt"

try:
    print(f"Subiendo a: {test_path}")
    response = client.storage.from_("Justificantes").upload(
        path=test_path,
        file=test_content
    )
    print(f"✅ Subida exitosa: {response}")

    # Limpiar
    client.storage.from_("Justificantes").remove([test_path])
    print("✅ Archivo de prueba eliminado")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST 5: Subir archivo con content-type en file_options")
print("=" * 60)

test_content = b"Contenido de prueba - test 5"
test_path = "pausas/user_999/test_with_options.txt"

try:
    print(f"Subiendo a: {test_path}")
    response = client.storage.from_("Justificantes").upload(
        path=test_path,
        file=test_content,
        file_options={
            "content-type": "text/plain"
        }
    )
    print(f"✅ Subida exitosa: {response}")

    # Limpiar
    client.storage.from_("Justificantes").remove([test_path])
    print("✅ Archivo de prueba eliminado")
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST 6: Verificar headers")
print("=" * 60)

try:
    storage_bucket = client.storage.from_("Justificantes")
    print(f"Headers del cliente: {storage_bucket._client.headers}")
    print(f"Base URL: {storage_bucket._base_url}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST 7: Verificar versión completa de httpx")
print("=" * 60)

try:
    import httpx
    print(f"httpx version: {httpx.__version__}")

    # Intentar hacer una petición simple
    test_client = httpx.Client()
    response = test_client.get("https://httpbin.org/headers")
    print(f"✅ Test de petición HTTP básica exitoso: {response.status_code}")
    test_client.close()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("Si todos los tests pasaron, el problema podría estar en:")
print("1. El servidor Flask no se reinició correctamente")
print("2. Hay algún problema con cómo Flask maneja el archivo multipart")
print("3. Hay un middleware o configuración de Flask que interfiere")
