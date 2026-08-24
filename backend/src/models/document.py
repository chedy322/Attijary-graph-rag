import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import db


class DocumentStatus(str, enum.Enum):
    PENDING_UPLOAD = "PENDING_UPLOAD"
    PROCESSING = "PROCESSING"
    ACTIVE_COMPLETED = "ACTIVE/COMPLETED"
    FAILED = "FAILED"
    PENDING_DELETE = "PENDING_DELETE"


class DocumentOrigin(str, enum.Enum):
    SCRAPED = "SCRAPED"
    MANUAL = "MANUAL"


class Document(db.Model):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    number = Column(String(100), nullable=True)
    # this date field is the publication date of the document, not the upload date
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    category = Column(String(100), nullable=True)
    file_path = Column(Text, nullable=False)
    file_extension = Column(String(10), nullable=False)
    status = Column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.PENDING_UPLOAD,
    )
    origin = Column(Enum(DocumentOrigin, name="document_origin"), nullable=False)
    source_url = Column(Text, nullable=True)
    uploaded_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    uploaded_by = relationship("User", back_populates="documents")

    def to_dict(self):
        return {
            "document_id": str(self.document_id),
            "title": self.title,
            "number": self.number,
            "date": self.date.isoformat() if self.date else None,
            "category": self.category,
            "file_path": self.file_path,
            "file_extension": self.file_extension,
            "status": self.status.value,
            "origin": self.origin.value,
            "source_url": self.source_url,
            "uploaded_by_user_id": str(self.uploaded_by_user_id)
            if self.uploaded_by_user_id
            else None,
        }
