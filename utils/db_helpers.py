"""
Helpers para manejo de transacciones y errores de base de datos.

CONVENCIÓN IMPORTANTE:
- Las vistas son RESPONSABLES de hacer db.session.commit() explícitamente
- El decorador @db_transaction SOLO hace:
  1. Capturar SQLAlchemyError
  2. Hacer rollback automático
  3. Loguear el error con contexto
  4. Retornar error al cliente (JSON o HTML según request)

Esto mantiene clara la responsabilidad de cada capa.
"""

from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from models.database import db
from flask import jsonify, request, flash, redirect, url_for
from utils.logging_utils import log_exception


def db_transaction(flash_error=True):
    """
    Decorador para manejar errores de transacciones DB automáticamente.

    CONVENCIÓN: Las vistas hacen db.session.commit() explícitamente.
    El decorador SOLO hace rollback + logging si hay excepción SQLAlchemy.

    Args:
        flash_error: Si True, muestra mensaje de error al usuario
                    Si False, re-lanza la excepción

    Returns:
        Función decorada que maneja excepciones SQLAlchemy

    Ejemplo:
        @app.route("/check_in", methods=["POST"])
        @db_transaction(flash_error=True)
        def check_in():
            new_rec = TimeRecord(...)
            db.session.add(new_rec)
            db.session.commit()  # ← Commit explícito (convención clara)
            flash("Entrada registrada correctamente.", "success")
            return redirect(url_for("time.dashboard_employee"))
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except SQLAlchemyError as e:
                # Hacer rollback automático
                db.session.rollback()

                # Loguear el error con contexto del endpoint
                log_exception(e, f"Database error in {f.__name__}")

                if flash_error:
                    # Diferenciar entre API (JSON) e HTML (forms)
                    if request.is_json:
                        return jsonify({
                            "success": False,
                            "error": "Error de base de datos. Intenta de nuevo."
                        }), 500
                    else:
                        flash("Error al procesar la operación. Intenta de nuevo.", "danger")
                        # Redirigir al referer o a la home para evitar respuestas vacías
                        return redirect(request.referrer or url_for("index"))
                else:
                    # Si flash_error=False, re-lanzar la excepción
                    raise

        return decorated_function
    return decorator
