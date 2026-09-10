from pydantic import BaseModel, EmailStr
from datetime import datetime
from models.audit_log import AuditLog
import uuid

class GetLogs(BaseModel):
    id: uuid.UUID
    action: str
    target_resource: str
    ip_address: str
    details: str
    created_at: datetime

    @classmethod
    def map(cls, audit_logs: AuditLog):
        try:
            return cls(
                id=audit_logs.id,
                action=audit_logs.action,
                target_resource=audit_logs.target_resource,
                ip_address=audit_logs.ip_address,
                details=audit_logs.details,
                created_at=audit_logs.created_at,
            )
        except Exception as e:
            raise ValueError(f"Error mapping audit log to GetLogs: {str(e)}")
