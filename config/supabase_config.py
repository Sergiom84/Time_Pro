"""
Configuración de Supabase Storage para almacenamiento de archivos
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gqesfclbingbihakiojm.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Para operaciones públicas
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Para operaciones de storage
# Fallback: usar SUPABASE_KEY si existe (para compatibilidad)
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

# Nombre del bucket de almacenamiento
STORAGE_BUCKET = "Justificantes"

# Configuración de archivos
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/jpg'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB en bytes

# Cliente de Supabase
_supabase_client = None


def get_supabase_client() -> Client:
    """
    Obtener cliente de Supabase (singleton)
    """
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_KEY no está configurada en las variables de entorno. "
                "Por favor, añade tu Service Role Key de Supabase en el archivo .env"
            )

        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _supabase_client


def init_storage_bucket():
    """
    Inicializar bucket de almacenamiento si no existe
    (Esto se ejecutará al iniciar la app)
    """
    try:
        client = get_supabase_client()

        # Intentar obtener el bucket
        buckets = client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]

        if STORAGE_BUCKET not in bucket_names:
            # Crear bucket si no existe
            client.storage.create_bucket(
                STORAGE_BUCKET,
                options={
                    "public": False,  # No público por defecto (requiere autenticación)
                    "file_size_limit": MAX_FILE_SIZE,
                    "allowed_mime_types": list(ALLOWED_MIME_TYPES)
                }
            )
            print(f"✅ Bucket '{STORAGE_BUCKET}' creado exitosamente")
        else:
            print(f"ℹ️  Bucket '{STORAGE_BUCKET}' ya existe")

    except Exception as e:
        print(f"⚠️  Error al inicializar bucket: {e}")
        print(f"   Puedes crear el bucket manualmente en Supabase Dashboard")
