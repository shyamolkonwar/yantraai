import redis
from rq import Queue
from app.core.config import settings

# Create Redis connection
redis_conn = redis.from_url(settings.REDIS_URL)

# Create queue
queue = Queue('yantra-ai-queue', connection=redis_conn)


def enqueue_job(job_id: str):
    """
    Enqueue a job for processing
    """
    from app.worker.process_document import process_document_job

    # Enqueue job with timeout
    job = queue.enqueue(
        process_document_job,
        job_id,
        timeout=settings.JOB_TIMEOUT_SECONDS
    )
    return job


def get_job_status(job_id: str):
    """
    Get the status of a background job
    """
    job = queue.fetch_job(job_id)
    if job:
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "enqueued_at": job.enqueued_at,
            "started_at": job.started_at,
            "ended_at": job.ended_at,
            "exc_info": job.exc_info
        }
    return None


def is_job_processing(job_id: str) -> bool:
    """
    Check if a job is currently being processed
    """
    job_status = get_job_status(job_id)
    if job_status:
        return job_status["status"] in ["queued", "started"]
    return False