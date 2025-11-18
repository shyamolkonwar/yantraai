#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.utils import generate_job_id, create_job_folder
from app.services.orchestrator import process_job

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/process_single.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    job_id = generate_job_id()
    job_dir = create_job_folder(job_id)

    # Copy file to job dir
    import shutil
    shutil.copy(pdf_path, os.path.join(job_dir, "original.pdf"))

    result = process_job(job_id, job_dir)
    print(f"Processed job {job_id}")
    print(f"Result saved to {os.path.join(job_dir, 'result.json')}")

if __name__ == "__main__":
    main()
