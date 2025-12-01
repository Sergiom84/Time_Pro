"""
Utilidades para manejo de archivos: validación, upload, download
"""
import os
import re
from io import BytesIO
# import magic  # Comentado temporalmente - requiere libmagic
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from config.supabase_config import (
    get_supabase_client,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    STORAGE_BUCKET
)
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def allowed_file(filename: str) -> bool:
    """
    Verificar si la extensión del archivo es permitida
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_filename(filename: str) -> str:
    """
    Sanitizar nombre de archivo para evitar problemas de seguridad
    """
    # Obtener extensión
    name, ext = os.path.splitext(filename)

    # Limpiar nombre
    name = secure_filename(name)

    # Limitar longitud
    if len(name) > 50:
        name = name[:50]

    # Añadir timestamp para evitar colisiones
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized = f"{name}_{timestamp}{ext}"

    return sanitized


def validate_file(file: FileStorage) -> tuple[bool, str]:
    """
    Validar archivo: tamaño, extensión, tipo MIME

    Returns:
        (es_valido, mensaje_error)
    """
    # Verificar que hay un archivo
    if not file or file.filename == '':
        return False, "No se ha seleccionado ningún archivo"

    # Verificar extensión
    if not allowed_file(file.filename):
        return False, f"Extensión no permitida. Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}"

    # Verificar tamaño
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Volver al inicio

    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return False, f"El archivo es demasiado grande. Tamaño máximo: {max_mb}MB"

    if file_size == 0:
        return False, "El archivo está vacío"

    # Verificar tipo MIME real (no solo extensión)
    # TEMPORALMENTE COMENTADO - requiere libmagic instalado
    # try:
    #     file_content = file.read(2048)  # Leer primeros 2KB
    #     file.seek(0)  # Volver al inicio
    #
    #     mime = magic.from_buffer(file_content, mime=True)
    #
    #     if mime not in ALLOWED_MIME_TYPES:
    #         return False, f"Tipo de archivo no permitido: {mime}"
    #
    # except Exception as e:
    #     print(f"⚠️  Error al verificar tipo MIME: {e}")
    #     # Si no se puede verificar el MIME, permitir basándose en extensión
    #     pass

    return True, ""


def upload_file_to_supabase(
    file: FileStorage,
    user_id: int,
    folder: str = "pausas"
) -> tuple[bool, str, dict]:
    """
    Subir archivo a Supabase Storage

    Args:
        file: Archivo a subir
        user_id: ID del usuario
        folder: Carpeta donde guardar (pausas o solicitudes)

    Returns:
        (exito, mensaje, datos)
        datos = {
            "url": "https://...",
            "filename": "nombre_original.pdf",
            "mime_type": "application/pdf",
            "size": 12345
        }
    """
    try:
        # Validar archivo
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            return False, error_msg, {}

        # Sanitizar nombre
        original_filename = file.filename
        sanitized_filename = sanitize_filename(original_filename)

        # Construir ruta en Supabase Storage
        storage_path = f"{folder}/user_{user_id}/{sanitized_filename}"

        # Leer contenido del archivo - asegurarse de estar al inicio
        file.seek(0)
        file_content = file.read()

        # Verificar que se leyó contenido
        if not file_content:
            return False, "El archivo está vacío o no se pudo leer", {}

        # Obtener tipo MIME basado en la extensión (temporalmente sin magic)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        mime_map = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        mime_type = mime_map.get(ext, 'application/octet-stream')

        # Subir a Supabase Storage usando requests directamente
        logger.debug("Intentando subir archivo: %s (tamano=%s bytes, mime=%s)", storage_path, len(file_content), mime_type)

        # Método alternativo usando requests directamente para evitar problemas con httpx
        try:
            import requests
            from config.supabase_config import SUPABASE_URL, SUPABASE_KEY

            upload_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}"

            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": mime_type,
                "x-upsert": "true"  # Sobrescribir si existe
            }

            logger.debug("URL: %s", upload_url)

            response = requests.post(
                upload_url,
                data=file_content,
                headers=headers,
                timeout=30
            )

            if response.status_code not in [200, 201]:
                error_detail = response.text
                logger.error("Error en upload - Status: %s Response: %s", response.status_code, error_detail)
                raise Exception(f"Error al subir archivo (status {response.status_code}): {error_detail}")

            logger.info("Archivo subido exitosamente - Status: %s", response.status_code)

        except Exception as upload_error:
            logger.error("Error en upload(): %s (%s)", upload_error, type(upload_error).__name__)
            raise

        # Generar signed URL manualmente usando requests
        logger.debug("Generando signed URL...")
        try:
            signed_url_api = f"{SUPABASE_URL}/storage/v1/object/sign/{STORAGE_BUCKET}/{storage_path}"
            sign_payload = {"expiresIn": 31536000}  # 1 año en segundos

            sign_response = requests.post(
                signed_url_api,
                json=sign_payload,
                headers={
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )

            if sign_response.status_code == 200:
                signed_data = sign_response.json()
                signed_path = signed_data.get('signedURL', '')
                final_url = f"{SUPABASE_URL}/storage/v1{signed_path}"
                logger.debug("Signed URL generada exitosamente")
            else:
                logger.warning("No se pudo generar signed URL, usando URL pública")
                final_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{storage_path}"

        except Exception as sign_error:
            logger.warning("Error al generar signed URL: %s, usando URL pública", sign_error)
            final_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{storage_path}"

        logger.debug("URL final: %s...", final_url[:100])


        return True, "Archivo subido exitosamente", {
            "url": final_url,
            "filename": original_filename,
            "mime_type": mime_type,
            "size": len(file_content)
        }

    except Exception as e:
        error_msg = f"{str(e)}"
        import traceback
        logger.error("Error al subir archivo: %s (%s)\n%s", error_msg, type(e).__name__, traceback.format_exc())
        return False, error_msg, {}


def delete_file_from_supabase(file_url: str) -> tuple[bool, str]:
    """
    Eliminar archivo de Supabase Storage

    Args:
        file_url: URL completa del archivo

    Returns:
        (exito, mensaje)
    """
    try:
        # Extraer path del archivo desde la URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/justificantes/pausas/user_1/file.pdf
        match = re.search(rf'{STORAGE_BUCKET}/(.+)', file_url)

        if not match:
            return False, "URL de archivo inválida"

        file_path = match.group(1)

        # Eliminar de Supabase Storage
        client = get_supabase_client()
        client.storage.from_(STORAGE_BUCKET).remove([file_path])

        return True, "Archivo eliminado exitosamente"

    except Exception as e:
        error_msg = f"Error al eliminar archivo: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_signed_url(file_url: str, expires_in: int = 3600) -> str:
    """
    Generar URL firmada para acceso temporal a archivo privado

    Args:
        file_url: URL del archivo
        expires_in: Tiempo de expiración en segundos (default: 1 hora)

    Returns:
        URL firmada
    """
    try:
        # Extraer path del archivo
        match = re.search(rf'{STORAGE_BUCKET}/(.+)', file_url)

        if not match:
            return file_url

        file_path = match.group(1)

        # Generar signed URL
        client = get_supabase_client()
        signed_url = client.storage.from_(STORAGE_BUCKET).create_signed_url(
            path=file_path,
            expires_in=expires_in
        )

        return signed_url.get('signedURL', file_url)

    except Exception as e:
        logger.error("Error al generar signed URL: %s", e)
        return file_url
