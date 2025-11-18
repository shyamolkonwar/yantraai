#!/usr/bin/env python3
"""
RQ Worker entry point
"""

import sys
import os
from rq import Worker

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.job_queue import redis_conn

if __name__ == '__main__':
    worker = Worker(['yantra-ai-queue'], connection=redis_conn)
    worker.work()
