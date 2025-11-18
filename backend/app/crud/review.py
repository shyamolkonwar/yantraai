from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.region import Region
from app.models.audit import AuditLog
from app.schemas.job import ReviewQueueItem
from app.core.config import settings


class ReviewCRUD:
    def get_review_queue(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20
    ) -> List[dict]:
        """
        Get regions needing human review (low trust scores and not human verified)
        """
        regions = db.query(Region).filter(
            and_(
                Region.trust_score < settings.TRUST_SCORE_THRESHOLD,
                Region.human_verified == False
            )
        ).order_by(desc(Region.created_at)).offset(skip).limit(limit).all()

        review_items = []
        for region in regions:
            # Get job info
            job = db.query(region.job).first()
            # Get page info
            page = db.query(region.page).first()

            review_items.append({
                "region_id": str(region.id),
                "job_id": str(region.job_id),
                "job_filename": job.original_filename if job else "Unknown",
                "page_number": page.page_number if page else 0,
                "bbox": region.bbox,
                "label": region.label,
                "raw_text": region.raw_text,
                "normalized_text": region.normalized_text,
                "trust_score": region.trust_score,
                "pii_detected": region.pii_detected
            })

        return review_items

    def review_region(
        self,
        db: Session,
        *,
        region_id: str,
        user_id: str,
        verified_value: Optional[str] = None,
        action: str
    ) -> Optional[AuditLog]:
        """
        Review a region and record the action
        """
        region = db.query(Region).filter(Region.id == region_id).first()
        if not region or region.human_verified:
            return None

        # Store before state
        before_state = {
            "normalized_text": region.normalized_text,
            "trust_score": region.trust_score,
            "human_verified": region.human_verified,
            "verified_value": region.verified_value
        }

        # Update region based on action
        if action == "correct" and verified_value:
            region.normalized_text = verified_value
            region.verified_value = verified_value
            region.trust_score = 1.0  # High confidence after human correction
        elif action == "approve":
            region.trust_score = max(region.trust_score, 0.9)  # High confidence after approval
        elif action == "skip":
            # Don't modify trust score for skipped items
            pass

        region.human_verified = True

        # Store after state
        after_state = {
            "normalized_text": region.normalized_text,
            "trust_score": region.trust_score,
            "human_verified": region.human_verified,
            "verified_value": region.verified_value
        }

        # Create audit log
        audit_log = AuditLog(
            job_id=region.job_id,
            region_id=region_id,
            user_id=user_id,
            action=action,
            before=before_state,
            after=after_state,
            notes=f"Region reviewed with action: {action}"
        )

        db.add(audit_log)
        db.add(region)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    def get_review_stats(self, db: Session) -> dict:
        """
        Get review statistics
        """
        total_regions = db.query(Region).count()
        verified_regions = db.query(Region).filter(Region.human_verified == True).count()
        pending_review = db.query(Region).filter(
            and_(
                Region.trust_score < settings.TRUST_SCORE_THRESHOLD,
                Region.human_verified == False
            )
        ).count()

        audit_stats = db.query(AuditLog).all()

        action_counts = {}
        for audit in audit_stats:
            action_counts[audit.action] = action_counts.get(audit.action, 0) + 1

        return {
            "total_regions": total_regions,
            "verified_regions": verified_regions,
            "pending_review": pending_review,
            "verification_rate": (verified_regions / total_regions * 100) if total_regions > 0 else 0,
            "action_breakdown": action_counts
        }


# Create CRUD instance
review_crud = ReviewCRUD()