import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func,Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    action = Column(String, nullable=False) #Example: "CREATE", "UPDATE", "DELETE","LOGIN","LOGOUT" etc...
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id",ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    target_resource = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    details= Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),default=datetime.utcnow, nullable=False)

    relationship("User", lazy="joined")
