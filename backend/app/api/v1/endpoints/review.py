from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.core.database import get_db
from app.deps.auth import get_current_reviewer_or_admin_user
from app.crud.review import review_crud
from app.models.user import User
from app.schemas.job import ReviewQueueItem, RegionReview
from app.schemas.audit import AuditLog

router = APIRouter()


@router.get("/queue", response_model=List[ReviewQueueItem])
async def get_review_queue(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_reviewer_or_admin_user),
    skip: int = 0,
    limit: int = 20
) -> Any:
    """
    Get queue of regions needing human review
    """
    regions = review_crud.get_review_queue(
        db=db,
        skip=skip,
        limit=limit
    )
    return regions


@router.post("/{region_id}", response_model=AuditLog)
async def review_region(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_reviewer_or_admin_user),
    region_id: str,
    review_data: RegionReview
) -> Any:
    """
    Review a specific region (approve, correct, or skip)
    """
    audit_log = review_crud.review_region(
        db=db,
        region_id=region_id,
        user_id=current_user.id,
        verified_value=review_data.verified_value,
        action=review_data.action
    )

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found or already reviewed"
        )

    return audit_log


@router.get("/stats")
async def get_review_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_reviewer_or_admin_user)
) -> Any:
    """
    Get review statistics
    """
    stats = review_crud.get_review_stats(db)
    return stats