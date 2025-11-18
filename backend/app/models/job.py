import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.core.database import Base


class JobStatus(PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    storage_path = Column(Text)  # S3 key or local path
    redacted_path = Column(Text)  # S3 key or local path for redacted PDF
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.QUEUED)
    error_message = Column(Text)
    progress = Column(String)  # Optional progress info
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="jobs")
    pages = relationship("Page", back_populates="job", cascade="all, delete-orphan")
    regions = relationship("Region", back_populates="job", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, filename={self.original_filename}, status={self.status})>"