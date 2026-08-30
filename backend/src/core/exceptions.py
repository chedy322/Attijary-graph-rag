import logging
from flask import Flask, jsonify, request, current_app
from werkzeug.exceptions import HTTPException

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


# def handle_exception(error):
#     # 1. Catch Custom Domain Errors
#     if isinstance(error, DomainError):
#         current_app.logger.error(f"DomainError: {error.message} (Status: {error.status_code})")
#         response = jsonify({"error": error.__class__.__name__, "message": error.message, "status": error.status_code})
#         response.status_code = error.status_code
#         return _add_cors_headers(response)

#     # 2. Catch Flask/HTTPExceptions (AppError, 401 Unauthorized, 404 Not Found, etc.)
#     if isinstance(error, HTTPException):
#         current_app.logger.error(f"HTTPException: {error.description} (Status Code: {error.code})")
#         response = jsonify({"error": error.name, "message": error.description, "status": error.code})
#         response.status_code = error.code
#         return _add_cors_headers(response)

#     # 3. Catch standard unhandled Python exceptions (500)
#     current_app.logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
#     response = jsonify({
#         "error": "Internal Server Error",
#         "message": str(error) if current_app.debug else "An unexpected server error occurred.",
#         "status": 500,
#     })
#     response.status_code = 500
#     return _add_cors_headers(response)
def handle_exception(error):
    # 1. Unroll tuple exceptions raised from shared service logic: raise Exception("msg", 400)
    if hasattr(error, "args") and len(error.args) == 2 and isinstance(error.args[1], int):
        message, status_code = error.args
        response = jsonify({
            "error": "Client Error" if status_code < 500 else "Server Error",
            "message": str(message),
            "status": status_code
        })
        response.status_code = status_code
        return _add_cors_headers(response)

    # 2. Catch Flask/HTTPExceptions (401, 403, 404, etc.)
    if isinstance(error, HTTPException):
        response = jsonify({
            "error": error.name,
            "message": error.description,
            "status": error.code
        })
        response.status_code = error.code
        return _add_cors_headers(response)

    # 3. Catch general unhandled exceptions (500)
    current_app.logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
    response = jsonify({
        "error": "Internal Server Error",
        "message": str(error),
        "status": 500
    })
    response.status_code = 500
    return _add_cors_headers(response)


def register_error_handlers(app: Flask):
    app.register_error_handler(Exception, handle_exception)