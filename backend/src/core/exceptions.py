from flask import Flask, render_template, jsonify, current_app
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base class for core logic errors."""

    pass


class VectorStoreError(DomainError):
    """Raised when Weaviate or vector operations fail."""

    def __init__(self, message="Vector store operation failed"):
        self.message = message
        super().__init__(self.message)
        logger.error(f"VectorStoreError: {self.message}")


class DocumentProcessingError(DomainError):
    """Raised when PDF extraction or chunking fails."""

    pass


class AppError(HTTPException):
    def __init__(self, message, status_code=500):
        self.description = message
        self.code = status_code
        super().__init__()


def handle_exception(error):
    if isinstance(error, HTTPException):
        current_app.logger.error(
            f"HTTPException: {error.description} (Status Code: {error.code})"
        )
        return jsonify(
            {"error": "Error", "message": error.description, "status": error.code}
        ), error.code

    response = {
        "error": "Internal Server Error",
        "message": "An unexpected server error occurred.",
        "status": 500,
    }
    current_app.logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
    return jsonify(response), 500


def register_error_handlers(app):
    app.register_error_handler(Exception, handle_exception)


# EXAMPLE USAGE for me later:raise AppError("This user account is suspended", 403)
