import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String)  # Path to the converted image
    width = Column(Integer)  # Image width
    height = Column(Integer)  # Image height
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="pages")
    regions = relationship("Region", back_populates="page", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Page(id={self.id}, job_id={self.job_id}, page_number={self.page_number})>"