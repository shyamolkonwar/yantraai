from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
import secrets


class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Yantra AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Authentication (can be disabled for testing)
    DISABLE_AUTH: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Supabase Configuration
    SUPABASE_URL: str = "https://lafzkdvjfnvlgiqiwfse.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxhZnprZHZqZm52bGdpcWl3ZnNlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0NDQ2NjUsImV4cCI6MjA3OTAyMDY2NX0.j7hFu5bae_DfIVRlHId26zWjBhv_Li58sTyAUKRYwFY"
    SUPABASE_SERVICE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxhZnprZHZqZm52bGdpcWl3ZnNlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzQ0NDY2NSwiZXhwIjoyMDc5MDIwNjY1fQ.SJ5KRP-K4434On6-RCkSarPNSzIfFs51NHcp7Ox00eQ"
    SUPABASE_STORAGE_URL: str = "https://lafzkdvjfnvlgiqiwfse.supabase.co/storage/v1"
    SUPABASE_BUCKET: str = "yantra-docs"

    # S3/Storage (fallback)
    S3_ENDPOINT: Optional[str] = "http://127.0.0.1:54321/storage/v1/s3"
    S3_ACCESS_KEY: Optional[str] = "625729a08b95bf1b7ff351a663f3a23c"
    S3_SECRET_KEY: Optional[str] = "850181e4652dd023b7a98c58ae0d2d34bd487ee0cc3254aed6eda37307425907"
    S3_BUCKET: Optional[str] = "yantra-docs"
    S3_USE_SSL: bool = False
    LOCAL_STORAGE_PATH: str = "./storage"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ML/OCR Settings
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    TRUST_SCORE_THRESHOLD: float = 0.6
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf"]

    # Worker settings
    WORKER_CONCURRENCY: int = 2
    JOB_TIMEOUT_SECONDS: int = 600  # 10 minutes

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
