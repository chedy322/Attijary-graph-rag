import enum
import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from config.database import db


class ConversationRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class Conversation(db.Model):
    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chats.chat_id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(Enum(ConversationRole, name="conversation_role"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    rag_source = Column(JSONB, nullable=True)

    # Relationships
    chat = relationship("Chat", back_populates="conversations")
