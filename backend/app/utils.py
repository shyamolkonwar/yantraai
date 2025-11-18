import os
import uuid
from datetime import datetime
import shutil

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs")

def generate_job_id() -> str:
    return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

def create_job_folder(job_id: str) -> str:
    job_dir = os.path.join(DATA_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(os.path.join(job_dir, "pages"), exist_ok=True)
    os.makedirs(os.path.join(job_dir, "regions"), exist_ok=True)
    return job_dir

def save_file_locally(job_id: str, file) -> str:
    job_dir = os.path.join(DATA_DIR, job_id)
    file_path = os.path.join(job_dir, "original.pdf")  # Assuming PDF for now
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path

def get_all_jobs() -> list:
    if not os.path.exists(DATA_DIR):
        return []
    return [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
