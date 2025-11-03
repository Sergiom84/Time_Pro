"""
Script para probar la subida de archivos a Supabase Storage
"""
from config.supabase_config import get_supabase_client, STORAGE_BUCKET, SUPABASE_KEY
import os

def test_supabase_connection():
    """Probar conexión con Supabase"""
    print("🧪 Probando conexión con Supabase Storage...")
    print(f"   Bucket: {STORAGE_BUCKET}")
    print(f"   Key configurada: {'Sí' if SUPABASE_KEY else 'No'}")
    print(f"   Key type: {'Service' if len(SUPABASE_KEY or '') > 200 else 'Anon' if SUPABASE_KEY else 'None'}")

    try:
        client = get_supabase_client()
        print("✅ Cliente de Supabase creado correctamente")

        # Listar buckets
        print("\n📦 Listando buckets disponibles...")
        buckets = client.storage.list_buckets()
        print(f"   Buckets encontrados: {len(buckets)}")
        for bucket in buckets:
            print(f"   - {bucket.name} (público: {bucket.public})")

        # Verificar si existe el bucket
        bucket_names = [b.name for b in buckets]
        if STORAGE_BUCKET in bucket_names:
            print(f"\n✅ Bucket '{STORAGE_BUCKET}' encontrado")
        else:
            print(f"\n⚠️  Bucket '{STORAGE_BUCKET}' NO encontrado")
            print(f"   Necesitas crear el bucket en Supabase Dashboard o ejecutar init_storage_bucket()")

        # Probar subida de archivo de prueba
        print("\n📤 Probando subida de archivo...")
        test_content = b"Test file content"
        test_path = "test/test_file.txt"

        try:
            response = client.storage.from_(STORAGE_BUCKET).upload(
                path=test_path,
                file=test_content,
                file_options={
                    "content-type": "text/plain",
                    "upsert": "true"
                }
            )
            print(f"✅ Archivo de prueba subido exitosamente")
            print(f"   Response: {response}")

            # Eliminar archivo de prueba
            client.storage.from_(STORAGE_BUCKET).remove([test_path])
            print(f"✅ Archivo de prueba eliminado")

        except Exception as upload_error:
            print(f"❌ Error al subir archivo de prueba:")
            print(f"   {str(upload_error)}")
            print(f"   Tipo: {type(upload_error).__name__}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")
        import traceback
        print(f"\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_supabase_connection()
