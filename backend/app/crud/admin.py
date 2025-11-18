import json
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus
from app.models.region import Region
from app.models.audit import AuditLog


class AdminCRUD:
    def export_job_data(self, db: Session, job_id: str) -> List[str]:
        """
        Export corrected field pairs for a specific job as JSONL
        """
        regions = db.query(Region).filter(
            and_(
                Region.job_id == job_id,
                Region.human_verified == True,
                Region.verified_value.isnot(None)
            )
        ).all()

        jsonl_lines = []
        for region in regions:
            training_data = {
                "job_id": str(region.job_id),
                "region_id": str(region.id),
                "original_text": region.raw_text,
                "verified_text": region.verified_value,
                "label": region.label,
                "bbox": region.bbox,
                "confidence": region.trust_score
            }
            jsonl_lines.append(json.dumps(training_data))

        return jsonl_lines

    def export_all_corrections(self, db: Session) -> List[str]:
        """
        Export all corrected field pairs as JSONL
        """
        regions = db.query(Region).filter(
            and_(
                Region.human_verified == True,
                Region.verified_value.isnot(None)
            )
        ).all()

        jsonl_lines = []
        for region in regions:
            training_data = {
                "job_id": str(region.job_id),
                "region_id": str(region.id),
                "original_text": region.raw_text,
                "verified_text": region.verified_value,
                "label": region.label,
                "bbox": region.bbox,
                "confidence": region.trust_score,
                "created_at": region.created_at.isoformat() if region.created_at else None
            }
            jsonl_lines.append(json.dumps(training_data))

        return jsonl_lines

    def get_admin_stats(self, db: Session) -> dict:
        """
        Get administrative statistics
        """
        # User stats
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
        reviewer_users = db.query(User).filter(User.role == UserRole.REVIEWER).count()

        # Job stats
        total_jobs = db.query(Job).count()
        completed_jobs = db.query(Job).filter(Job.status == JobStatus.DONE).count()
        failed_jobs = db.query(Job).filter(Job.status == JobStatus.FAILED).count()
        processing_jobs = db.query(Job).filter(Job.status == JobStatus.PROCESSING).count()

        # Region stats
        total_regions = db.query(Region).count()
        verified_regions = db.query(Region).filter(Region.human_verified == True).count()
        avg_trust_score = db.query(func.avg(Region.trust_score)).filter(Region.trust_score.isnot(None)).scalar() or 0

        # PII stats
        regions_with_pii = db.query(Region).filter(Region.pii_detected.isnot(None)).count()

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "admin": admin_users,
                "reviewer": reviewer_users
            },
            "jobs": {
                "total": total_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "processing": processing_jobs,
                "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            },
            "regions": {
                "total": total_regions,
                "verified": verified_regions,
                "verification_rate": (verified_regions / total_regions * 100) if total_regions > 0 else 0,
                "avg_trust_score": float(avg_trust_score),
                "regions_with_pii": regions_with_pii
            }
        }


# Create CRUD instance
admin_crud = AdminCRUD()