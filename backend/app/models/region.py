import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    bbox = Column(JSONB, nullable=False)  # {x1, y1, x2, y2}
    label = Column(String, nullable=False)  # paragraph, table, signature, header, handwritten
    raw_text = Column(Text)
    ocr_confidence = Column(Float)  # OCR confidence score (0-1)
    normalized_text = Column(Text)
    translation_confidence = Column(Float)  # Translation/normalization confidence (0-1)
    pii_detected = Column(JSONB)  # [{entity, start, end, confidence}]
    trust_score = Column(Float)  # Overall trust score (0-1)
    human_verified = Column(Boolean, default=False)
    verified_value = Column(Text)  # Human-corrected value
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job = relationship("Job", back_populates="regions")
    page = relationship("Page", back_populates="regions")
    audit_logs = relationship("AuditLog", back_populates="region", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Region(id={self.id}, label={self.label}, trust_score={self.trust_score})>"