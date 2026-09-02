


from typing import Any, Dict
import requests
import os
import logging
from flask import Flask,request
logger = logging.getLogger(__name__)
N8N_WEBHOOK_URL=os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")
def send_n8n_webhook(error_type, message, status_code, stack_trace=None):
    payload = {
        "error_type": error_type,
        "message": message,
        "status_code": status_code,
        "stack_trace": stack_trace,
        "service_name": "graphRag",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "request_url": request.url,
        "request_method": request.method,

    }
    if not N8N_WEBHOOK_URL:
        raise ValueError("N8N_WEBHOOK_URL is not set")
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        response.raise_for_status()  #
    except requests.RequestException as e:
        logger.error(f"Failed to send webhook: {e}")
        raise ValueError(f"Failed to send webhook: {e}")