
from services.dto.get_audit_log_dto import GetLogs
from models.audit_log import AuditLog
from config import db
from typing import List, Dict, Any
import logging
logger = logging.getLogger(__name__)
class AuditService:
    def __init__(self, db=db):
        self.db = db

    def batch_store_logs(self,logs:List[Dict[str,Any]])->Dict[str,Any]:
       
       if not logs:
           logger.info("[audit_logs] No logs to store. Exiting batch_store_logs.")
           return {"status": "error", "message": "No logs to store."}
       try:
            logger.info(f"[audit_logs] Storing {len(logs)} audit logs in batch.")
            self.db.session.bulk_insert_mappings(AuditLog, logs)
            self.db.session.commit()
            return {"status": "success", "message": f"Stored {len(logs)} audit logs successfully."}
       except Exception as e:
            logger.error(f"[audit_logs] Error while storing audit logs: {e}")
            self.db.session.rollback()
            raise e
    def create_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a single audit log entry in the database.

        Args:
            log_data: A dictionary containing the audit log details.

        Returns:
            A dictionary indicating the success or failure of the operation.
        """
        try:
            if not log_data:
                logger.info("[audit_logs] No log data provided. Exiting create_log.")
                return {"status": "error", "message": "No log data provided."}
            logger.info(f"[audit_logs] Creating a single audit log entry: {log_data}")
            new_log = AuditLog(**log_data)
            self.db.session.add(new_log)
            self.db.session.commit()
            return {"status": "success", "message": "Audit log created successfully."}
        except Exception as e:
            logger.error(f"[audit_logs] Error while creating audit log: {e}")
            self.db.session.rollback()
            raise e
    def find_log_by_id(self, log_id: str) -> AuditLog:
        """
        Find an audit log entry by its ID.

        Args:
            log_id: The ID of the audit log to find.

        Returns:
            The AuditLog object if found, otherwise None.
        """
        try:
            if not log_id:
                logger.info("[audit_logs] No log ID provided. Exiting find_log_by_id.")
                return None
            logger.info(f"[audit_logs] Searching for audit log with id: {log_id}")
            return self.db.session.query(AuditLog).filter_by(id=log_id).first()
        except Exception as e:
            logger.error(f"[audit_logs] Error while searching for audit log with id {log_id}: {e}")
            raise e

    def find_all_logs(self,limit=10,offset=0) -> List[GetLogs]:
        """
        Retrieve all audit log entries from the database.

        Returns:
            A list of AuditLog objects.
        """
        try:
            logger.info("[audit_logs] Retrieving all audit logs.")
            all_logs=self.db.session.query(AuditLog).offset(offset).limit(limit).all()
            # Transfer the returned result to DTO
            returned_logs=[GetLogs.map(log) for log in all_logs]
            return returned_logs
        except Exception as e:
            logger.error(f"[audit_logs] Error while retrieving all audit logs: {e}")
            raise e

audit_service = AuditService()