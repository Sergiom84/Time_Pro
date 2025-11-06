"""
Configuracion de Supabase Storage para almacenamiento de archivos.
Requiere variables de entorno: SUPABASE_URL y SUPABASE_KEY (service o anon).
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configuracion de Supabase (obligatorio por entorno)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Para operaciones publicas
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Para operaciones de storage
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

# Nombre del bucket de almacenamiento
STORAGE_BUCKET = "Justificantes"

# Configuracion de archivos
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/jpg",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB en bytes

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Obtener cliente de Supabase (singleton)."""
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL:
            raise ValueError(
                "SUPABASE_URL no esta configurada en las variables de entorno."
            )
        if not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_KEY (o SUPABASE_SERVICE_KEY / SUPABASE_ANON_KEY) no esta configurada."
            )
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _supabase_client


def init_storage_bucket():
    """
    Inicializar bucket de almacenamiento si no existe.
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
                    "public": False,
                    "file_size_limit": MAX_FILE_SIZE,
                    "allowed_mime_types": list(ALLOWED_MIME_TYPES),
                },
            )
            print(f"✓ Bucket '{STORAGE_BUCKET}' creado exitosamente")
        else:
            print(f"• Bucket '{STORAGE_BUCKET}' ya existe")

    except Exception as e:
        print(f"[storage] Error al inicializar bucket: {e}")
        print("   Puedes crearlo manualmente en Supabase Dashboard")

