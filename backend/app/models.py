"""SQLAlchemy ORM models for the Document Intelligence application."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


class DocumentStatus(str, enum.Enum):
    """Processing pipeline status for a document."""

    UPLOADING = "uploading"
    PARSING = "parsing"
    CLASSIFYING = "classifying"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class Document(Base):
    """Represents an uploaded document and its processing state."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    original_filename = Column(String(512), nullable=False)
    stored_filename = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_time = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status = Column(
        Enum(DocumentStatus),
        default=DocumentStatus.UPLOADING,
        nullable=False,
    )
    classification_json = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    pages = relationship(
        "Page", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.original_filename}, status={self.status})>"


class Page(Base):
    """Represents a single page extracted from a document."""

    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=True)
    has_tables = Column(Boolean, default=False)
    tables_json = Column(Text, nullable=True)
    image_path = Column(String(1024), nullable=True)
    ocr_used = Column(Boolean, default=False)
    ocr_confidence = Column(Float, nullable=True)

    document = relationship("Document", back_populates="pages")

    def __repr__(self) -> str:
        return f"<Page(id={self.id}, doc={self.document_id}, page={self.page_number})>"


class ChatMessage(Base):
    """Stores a single chat message (user or assistant) for a conversation session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, session={self.session_id}, role={self.role})>"
