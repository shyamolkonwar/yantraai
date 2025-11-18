# Placeholder for async worker
# For MVP, processing is synchronous

def process_async(job_id: str, job_dir: str):
    from app.services.orchestrator import process_job
    return process_job(job_id, job_dir)
