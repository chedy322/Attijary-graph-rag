import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import db


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(db.Model):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.USER
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    clerk_id = Column(String(255), unique=True, nullable=False, index=True)

    # Relationships
    documents = relationship("Document", back_populates="uploaded_by")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
