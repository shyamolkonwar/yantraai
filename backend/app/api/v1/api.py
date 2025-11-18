from fastapi import APIRouter

from app.api.v1.endpoints import auth, jobs, review, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(review.router, prefix="/review", tags=["review"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])