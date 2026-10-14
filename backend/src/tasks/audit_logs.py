import logging
from celery import shared_task
from typing import Dict, Any
from services.audit_service import audit_service
logger = logging.getLogger(__name__)

@shared_task(max_retries=3, default_retry_delay=60, name="tasks.audit_log_task", bind=True)
def audit_log_task(self,audit_payload: Dict[str, Any]):    
        """
        Celery task: Audit log task for logging audit events.

        Args:
            audit_payload: A dictionary containing the audit log details.
        """
        try:
            if not audit_payload:
                logger.info("[audit_logs] No audit payload provided. Exiting Audit_log_Task.")
                return {"status": "error", "message": "No audit payload provided."}
            # Ensure idempotency by checking if the log already exists in the database
            existing_log=audit_service.find_log_by_id(audit_payload.get("id"))
            if existing_log:
                logger.info(f"[audit_logs] Audit log with id {audit_payload.get('id')} already exists. Skipping creation.")
                return {"status": "success", "message": f"Audit log with id {audit_payload.get('id')} already exists."}
            # Log the audit event using the provided payload
            logger.info(f"[audit_logs] Audit log event: {audit_payload}")
            # Store the audit log in the database
            audit_service.create_log(audit_payload)
            return {"status": "success", "message": "Audit log processed successfully."}
        except Exception as e:
            logger.error(f"[audit_logs] Error while processing audit log: {e}")
            raise e
