from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class AuditLogBase(BaseModel):
    action: str
    notes: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    job_id: str
    region_id: Optional[str] = None
    user_id: str
    before: Optional[dict] = None
    after: Optional[dict] = None


class AuditLog(AuditLogBase):
    id: str
    job_id: str
    region_id: Optional[str] = None
    user_id: str
    before: Optional[dict] = None
    after: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True