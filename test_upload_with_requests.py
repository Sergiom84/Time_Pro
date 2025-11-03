"""
Script para probar upload usando requests directamente
"""
import requests
from io import BytesIO
from werkzeug.datastructures import FileStorage
from config.supabase_config import SUPABASE_URL, SUPABASE_KEY, STORAGE_BUCKET

def test_upload_with_requests():
    """Probar upload de archivo usando requests"""
    print("🧪 Probando upload con requests...")

    # Crear archivo de prueba
    test_content = b"PDF content test " * 100
    storage_path = "test/test_upload.pdf"

    try:
        # Upload
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}"

        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/pdf",
            "x-upsert": "true"
        }

        print(f"📤 Subiendo a: {upload_url}")

        response = requests.post(
            upload_url,
            data=test_content,
            headers=headers,
            timeout=30
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")

        if response.status_code in [200, 201]:
            print("✅ Upload exitoso")

            # Probar signed URL
            print("\n📝 Generando signed URL...")
            signed_url_api = f"{SUPABASE_URL}/storage/v1/object/sign/{STORAGE_BUCKET}/{storage_path}"
            sign_payload = {"expiresIn": 3600}

            sign_response = requests.post(
                signed_url_api,
                json=sign_payload,
                headers={
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            print(f"Sign Status: {sign_response.status_code}")
            print(f"Sign Response: {sign_response.text[:200]}")

            if sign_response.status_code == 200:
                signed_data = sign_response.json()
                print(f"✅ Signed URL generada: {signed_data}")

            # Eliminar archivo de prueba
            delete_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}"
            delete_response = requests.delete(
                delete_url,
                headers={"Authorization": f"Bearer {SUPABASE_KEY}"},
                timeout=10
            )
            print(f"\n🗑️  Eliminación: {delete_response.status_code}")

        else:
            print(f"❌ Error en upload: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_upload_with_requests()
