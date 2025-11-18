from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.jobs import router as jobs_router
from app.api.review import router as review_router
from app.api.health import router as health_router


app = FastAPI(
    title="Truth Layer Backend",
    version="1.0.0",
    description="Local document processing and OCR API"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
app.include_router(review_router, prefix="/api/v1", tags=["review"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
