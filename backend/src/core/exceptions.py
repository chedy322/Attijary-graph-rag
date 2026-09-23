import logging
import traceback
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from webhooks.n8n_send_logs import send_n8n_webhook

# Standard module logger - captures the module name in structured logs
logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base class for core logic errors."""
    def __init__(self, message="A domain error occurred", status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class VectorStoreError(DomainError):
    """Raised when Weaviate or vector operations fail."""
    def __init__(self, message="Vector store operation failed"):
        logger.error(f"VectorStoreError: {message}")
        super().__init__(message=message, status_code=502)


class DocumentProcessingError(DomainError):
    """Raised when PDF extraction or chunking fails."""
    def __init__(self, message="Document processing failed"):
        super().__init__(message=message, status_code=422)


class AppError(HTTPException):
    def __init__(self, message, status_code=500):
        self.description = message
        self.code = status_code
        super().__init__()


def _add_cors_headers(response):
    """Utility helper to ensure browser receives CORS headers during errors."""
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


def handle_exception(error):
    # 1. Tuple exceptions raised from shared service logic: raise Exception("msg", 400)
    if hasattr(error, "args") and len(error.args) == 2 and isinstance(error.args[1], int):
        message, status_code = error.args
        error_type = "Client Error" if status_code < 500 else "Server Error (Tuple)"
        
        if status_code >= 500:
            logger.error(f"Server Error Tuple ({status_code}): {message}", exc_info=True)
            _safe_send_webhook(error_type, message, status_code)

        response = jsonify({
            "error": error_type,
            "message": str(message),
            "status": status_code
        })
        response.status_code = status_code
        return _add_cors_headers(response)

    # 2. Catch Flask/HTTPExceptions (401, 403, 404, 500, etc.)
    if isinstance(error, HTTPException):
        if error.code and error.code >= 500:
            logger.error(f"HTTPException ({error.code}): {error.description}", exc_info=True)
            _safe_send_webhook(error.name, error.description, error.code)
        else:
            logger.warning(f"HTTPException ({error.code}): {error.description}")

        response = jsonify({
            "error": error.name,
            "message": error.description,
            "status": error.code
        })
        response.status_code = error.code
        return _add_cors_headers(response)

    # 3. Catch general unhandled Python exceptions (500)
    logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
    _safe_send_webhook(error.__class__.__name__, str(error), 500)

    response = jsonify({
        "error": "Internal Server Error",
        "message": str(error),
        "status": 500
    })
    response.status_code = 500
    return _add_cors_headers(response)


def _safe_send_webhook(error_type: str, message: str, status_code: int):
    """Helper to ensure webhook errors don't crash the exception handler."""
    try:
        send_n8n_webhook(
            error_type=error_type,
            message=message,
            status_code=status_code,
            stack_trace=traceback.format_exc()
        )
    except Exception as e:
        logger.error(f"Failed to send n8n error notification webhook: {e}")


def register_error_handlers(app: Flask):
    app.register_error_handler(Exception, handle_exception)