from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.db.session import Base
import uuid
import enum
from app.core.config import settings

class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    validating = "validating"
    extracting_text = "extracting_text"
    ocr_processing = "ocr_processing"
    chunking = "chunking"
    generating_embeddings = "generating_embeddings"
    indexing = "indexing"
    completed = "completed"
    completed_with_warnings = "completed_with_warnings"
    failed = "failed"

class ExtractionMethod(str, enum.Enum):
    text = "text"
    ocr = "ocr"
    mixed = "mixed"

class PageExtractionMethod(str, enum.Enum):
    text = "text"
    ocr = "ocr"
    failed = "failed"
    empty = "empty"

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_hash = Column(String, nullable=False)
    page_count = Column(Integer, nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploaded, nullable=False)
    extraction_method = Column(Enum(ExtractionMethod), nullable=True)
    ocr_status = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    warnings = Column(JSONB, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('owner_id', 'content_hash', name='uix_owner_content_hash'),
    )

class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    page_number = Column(Integer, nullable=False)
    extraction_method = Column(Enum(PageExtractionMethod), nullable=False)
    ocr_confidence = Column(Float, nullable=True)
    text = Column(Text, nullable=True)
    warnings = Column(JSONB, nullable=True)
    status = Column(String, nullable=True)

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    document_name = Column(String, nullable=False)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    extraction_method = Column(Enum(ExtractionMethod), nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    embedding = Column(Vector(384))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
