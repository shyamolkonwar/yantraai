from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate


class JobCRUD:
    def get(self, db: Session, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return db.query(Job).filter(Job.id == job_id).first()

    def get_multi(self, db: Session, *, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get multiple jobs"""
        query = db.query(Job)
        if user_id:
            query = query.filter(Job.user_id == user_id)
        return query.order_by(desc(Job.created_at)).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: JobCreate, user_id: str) -> Job:
        """Create new job"""
        db_obj = Job(
            user_id=user_id,
            original_filename=obj_in.original_filename,
            status=JobStatus.QUEUED
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Job, obj_in: JobUpdate) -> Job:
        """Update job"""
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, job_id: str) -> bool:
        """Delete job (soft delete by setting status to deleted)"""
        job = self.get(db, job_id=job_id)
        if job:
            db.delete(job)
            db.commit()
            return True
        return False

    def get_user_job(self, db: Session, *, job_id: str, user_id: str) -> Optional[Job]:
        """Get job by ID for specific user"""
        return db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()


# Create CRUD instance
job_crud = JobCRUD()