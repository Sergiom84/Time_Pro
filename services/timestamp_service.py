"""
Servicio de sellado de tiempo y firma digital para fichajes.
Cumple con requisitos de la Ley de Fichajes sobre registros infalsificables.
"""
import hashlib
import hmac
import os
from datetime import datetime
from typing import Dict, Tuple
from flask import current_app


class TimestampService:
    """
    Servicio para generar y verificar sellos de tiempo con firma digital.

    Usa SHA-256 para hashing y HMAC-SHA256 para firma.
    Soporta rotación de claves mediante versiones.
    """

    @staticmethod
    def get_signing_key(version: int = 1) -> bytes:
        """
        Obtiene la clave HMAC según la versión.

        Args:
            version: Versión de la clave (default: 1)

        Returns:
            bytes: Clave de firma en bytes

        Raises:
            ValueError: Si la clave no existe en las variables de entorno
        """
        key_var = f"SIGNING_KEY_V{version}"
        key = os.getenv(key_var)

        if not key:
            current_app.logger.error(f"Missing {key_var} in environment variables")
            raise ValueError(
                f"Missing {key_var} in environment. "
                f"Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        return key.encode('utf-8')

    @staticmethod
    def generate_content_hash(data: Dict[str, any]) -> str:
        """
        Genera hash SHA-256 del contenido en orden determinista.

        Args:
            data: Diccionario con los datos a hashear

        Returns:
            str: Hash SHA-256 en formato hexadecimal (64 caracteres)
        """
        # Orden alfabético de claves para consistencia
        ordered_items = sorted(data.items())
        content = "|".join(f"{k}:{v}" for k, v in ordered_items)

        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return hash_obj.hexdigest()

    @staticmethod
    def sign_hash(content_hash: str, key_version: int = 1) -> str:
        """
        Firma el hash con HMAC-SHA256.

        Args:
            content_hash: Hash SHA-256 a firmar (hex string)
            key_version: Versión de la clave a usar (default: 1)

        Returns:
            str: Firma HMAC-SHA256 en formato hexadecimal (64 caracteres)
        """
        key = TimestampService.get_signing_key(key_version)
        signature = hmac.new(key, content_hash.encode('utf-8'), hashlib.sha256)
        return signature.hexdigest()

    @staticmethod
    def verify_signature(content_hash: str, signature: str, key_version: int) -> bool:
        """
        Verifica la firma de un registro.

        Args:
            content_hash: Hash del contenido original
            signature: Firma a verificar
            key_version: Versión de la clave usada

        Returns:
            bool: True si la firma es válida, False en caso contrario
        """
        try:
            expected_signature = TimestampService.sign_hash(content_hash, key_version)
            # Comparación timing-safe para prevenir ataques de tiempo
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            current_app.logger.error(f"Error verifying signature: {str(e)}")
            return False

    @staticmethod
    def create_signature_data(
        time_record_id: int,
        user_id: int,
        client_id: int,
        action: str,
        timestamp_utc: datetime,
        terminal_id: str
    ) -> Dict[str, any]:
        """
        Crea el diccionario de datos que será hasheado.

        Args:
            time_record_id: ID del TimeRecord
            user_id: ID del usuario
            client_id: ID del cliente
            action: "check_in" o "check_out"
            timestamp_utc: Timestamp UTC preciso
            terminal_id: Identificador del terminal (ej: "web_192.168.1.1")

        Returns:
            Dict: Diccionario ordenable con los datos
        """
        return {
            "time_record_id": time_record_id,
            "user_id": user_id,
            "client_id": client_id,
            "action": action,
            "timestamp_utc": timestamp_utc.isoformat(),
            "terminal_id": terminal_id
        }

    @staticmethod
    def seal_record(
        time_record,
        action: str,
        request,
        key_version: int = 1
    ) -> Tuple[str, str, datetime, str]:
        """
        Genera el sello completo para un fichaje (hash + firma).

        Args:
            time_record: Instancia de TimeRecord
            action: "check_in" o "check_out"
            request: Flask request object (para IP y User-Agent)
            key_version: Versión de la clave a usar (default: 1)

        Returns:
            Tuple: (content_hash, signature, timestamp_utc, terminal_id)
        """
        # Timestamp preciso en UTC
        timestamp_utc = datetime.utcnow()

        # Identificador del terminal
        ip_address = request.remote_addr or "unknown"
        terminal_id = f"web_{ip_address}"

        # Crear datos para hashear
        data = TimestampService.create_signature_data(
            time_record_id=time_record.id,
            user_id=time_record.user_id,
            client_id=time_record.client_id,
            action=action,
            timestamp_utc=timestamp_utc,
            terminal_id=terminal_id
        )

        # Generar hash y firma
        content_hash = TimestampService.generate_content_hash(data)
        signature = TimestampService.sign_hash(content_hash, key_version)

        current_app.logger.info(
            f"Sealed {action} for TimeRecord {time_record.id} "
            f"(User {time_record.user_id}, Client {time_record.client_id})"
        )

        return content_hash, signature, timestamp_utc, terminal_id

    @staticmethod
    def verify_record_signature(signature_record) -> bool:
        """
        Verifica la integridad de un registro de firma.

        Args:
            signature_record: Instancia de TimeRecordSignature

        Returns:
            bool: True si la firma es válida y el registro no ha sido alterado
        """
        # Recrear los datos originales
        data = TimestampService.create_signature_data(
            time_record_id=signature_record.time_record_id,
            user_id=signature_record.time_record.user_id,
            client_id=signature_record.client_id,
            action=signature_record.action,
            timestamp_utc=signature_record.timestamp_utc,
            terminal_id=signature_record.terminal_id
        )

        # Verificar que el hash coincide
        expected_hash = TimestampService.generate_content_hash(data)
        if expected_hash != signature_record.content_hash:
            current_app.logger.warning(
                f"Hash mismatch for signature {signature_record.id}: "
                f"expected {expected_hash}, got {signature_record.content_hash}"
            )
            return False

        # Verificar la firma
        return TimestampService.verify_signature(
            content_hash=signature_record.content_hash,
            signature=signature_record.signature,
            key_version=signature_record.key_version
        )
