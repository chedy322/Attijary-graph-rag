# backend/logging_config.py
import logging
import sys
import time
from flask import request, g
from pythonjsonlogger import jsonlogger


def configure_logging(app):
    """Configures structured JSON logging for Flask applications."""

    # 1. Create JSON Formatter
    json_formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(levelname)s %(name)s %(message)s %(module)s %(lineno)d"
    )

    # Add custom fields to logger (e.g., adding timestamp)
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            log_record["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            log_record["level"] = record.levelname.lower()

            # Inject user ID if available in Flask g context
            if g and getattr(g, "user_id", None):
                log_record["user_id"] = g.user_id

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomJsonFormatter("%(timestamp)s %(level)s %(message)s"))

    # 2. Attach Handler to App Logger
    app.logger.handlers.clear()  # Remove default Flask handler
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # 3. Add Request Timing Middleware
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request_info(response):
        # Calculate response time
        latency_ms = round(
            (time.time() - getattr(g, "start_time", time.time())) * 1000, 2
        )

        # Avoid logging noisy health check endpoints if you have them
        if request.path in ["/health", "/metrics"]:
            return response

        log_payload = {
            "event": "http_request",
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": latency_ms,
            "ip": request.remote_addr,
            "user_agent": request.user_agent.string,
        }

        # Log appropriate level based on HTTP status
        if response.status_code >= 500:
            app.logger.error("Request failed with server error", extra=log_payload)
        elif response.status_code >= 400:
            app.logger.warning("Request rejected", extra=log_payload)
        else:
            app.logger.info("Request processed successfully", extra=log_payload)

        return response
