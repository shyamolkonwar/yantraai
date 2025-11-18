from fastapi import APIRouter, HTTPException
import os
import json
from typing import List

from app.schemas import ReviewItem, ReviewCorrection
from app.utils import get_all_jobs

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "jobs")

@router.get("/review/queue", response_model=List[ReviewItem])
async def get_review_queue(limit: int = 20):
    queue = []
    jobs = get_all_jobs()

    for job_id in jobs:
        job_dir = os.path.join(DATA_DIR, job_id)
        result_path = os.path.join(job_dir, "result.json")

        if os.path.exists(result_path):
            with open(result_path, 'r') as f:
                result = json.load(f)

            for field in result.get("fields", []):
                if field.get("trust_score", 1.0) < 0.6 and not field.get("human_verified", False):
                    queue.append(ReviewItem(
                        job_id=job_id,
                        region_id=field["region_id"],
                        page=field["page"],
                        bbox=field["bbox"],
                        raw_text=field["raw_text"],
                        normalized_text=field["normalized_text"],
                        trust_score=field["trust_score"],
                        pii=field.get("pii", [])
                    ))

    # Sort by trust_score ascending (lowest first)
    queue.sort(key=lambda x: x.trust_score)

    return queue[:limit]

@router.post("/review/{job_id}/{region_id}")
async def submit_correction(job_id: str, region_id: str, correction: ReviewCorrection):
    job_dir = os.path.join(DATA_DIR, job_id)
    result_path = os.path.join(job_dir, "result.json")
    audit_path = os.path.join(job_dir, "audit.jsonl")

    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Job result not found")

    with open(result_path, 'r') as f:
        result = json.load(f)

    # Find and update the field
    for field in result.get("fields", []):
        if field["region_id"] == region_id:
            field["human_verified"] = True
            field["verified_value"] = correction.verified_value
            field["trust_score"] = 1.0
            break
    else:
        raise HTTPException(status_code=404, detail="Region not found")

    # Save updated result
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)

    # Append to audit log
    audit_entry = {
        "timestamp": correction.timestamp.isoformat() if hasattr(correction.timestamp, 'isoformat') else str(correction.timestamp),
        "user": correction.user,
        "region_id": region_id,
        "action": "correct",
        "before": field["raw_text"],
        "after": correction.verified_value
    }

    with open(audit_path, 'a') as f:
        f.write(json.dumps(audit_entry) + "\n")

    return {"status": "success"}
