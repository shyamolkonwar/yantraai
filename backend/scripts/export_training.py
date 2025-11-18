#!/usr/bin/env python3
import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.utils import get_all_jobs

def main():
    jobs = get_all_jobs()
    training_data = []

    for job_id in jobs:
        job_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs", job_id)
        audit_path = os.path.join(job_dir, "audit.jsonl")

        if os.path.exists(audit_path):
            with open(audit_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    training_item = {
                        "job_id": job_id,
                        "region_id": entry["region_id"],
                        "page": 1,  # TODO: get from result
                        "bbox": [],  # TODO: get from result
                        "raw_text": entry["before"],
                        "normalized_text": entry["before"],  # TODO: normalize
                        "verified_value": entry["after"]
                    }
                    training_data.append(training_item)

    # Write to training.jsonl
    with open("training.jsonl", 'w') as f:
        for item in training_data:
            f.write(json.dumps(item) + "\n")

    print(f"Exported {len(training_data)} training items to training.jsonl")

if __name__ == "__main__":
    main()
