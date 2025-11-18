# Yantra AI Backend

A comprehensive document processing and OCR backend that transforms messy scanned documents into structured JSON with field-level trust scores, PII redaction, and human review capabilities.

## Features

- **Multi-language OCR Support**: Advanced OCR with support for printed and handwritten text, including Indic languages
- **Intelligent Layout Detection**: Automatic detection and processing of different document regions (text, tables, headers, signatures)
- **Text Normalization**: Text cleaning, normalization, and transliteration for Indic languages
- **PII Detection & Redaction**: Automated detection of personally identifiable information with customizable redaction
- **Trust Score Evaluation**: Field-level confidence scoring to determine when human review is needed
- **Human-in-the-Loop**: Review queue for low-confidence fields with audit logging
- **Background Processing**: Scalable asynchronous document processing with Redis and RQ
- **RESTful API**: Complete REST API with authentication, role-based access control, and comprehensive endpoints
- **Docker Support**: Full containerization with docker-compose for easy deployment

## Architecture

### High-Level Components

1. **API Gateway (FastAPI)**: REST endpoints for document upload, job status, results, and review
2. **Orchestrator**: Manages document processing workflow and enqueues background jobs
3. **Background Workers**: Process documents through the ML/OCR pipeline using Redis Queue (RQ)
4. **Storage Layer**: File storage for original and processed documents (S3 compatible)
5. **Database**: PostgreSQL for metadata, job tracking, and audit logs
6. **Review Service**: Human review interface and workflow management

### Processing Pipeline

1. **K-Ingest**: PDF → images → layout detection → region extraction
2. **K-Lingua**: Text normalization, transliteration, and language processing
3. **K-Comply**: PII detection and redaction metadata generation
4. **K-Eval**: Trust score computation and routing decisions

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Queue**: Redis + Redis Queue (RQ)
- **Storage**: S3 compatible (MinIO for development)
- **OCR**: HuggingFace TrOCR, OpenCV
- **Layout Detection**: LayoutParser
- **PII Detection**: Microsoft Presidio + custom regex
- **Indic NLP**: AI4Bharat models and transliteration
- **Containerization**: Docker + Docker Compose
- **Authentication**: JWT with role-based access control

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd yantra-ai/backend
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database**:
   ```bash
   docker-compose exec web python cli.py migrate
   docker-compose exec web python cli.py create-user
   ```

4. **Access services**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - **Supabase Studio**: http://localhost:54323
   - **Supabase API Gateway**: http://localhost:54321
   - RQ Dashboard: http://localhost:9181

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services** (Supabase, Redis):
   ```bash
   docker-compose up -d supabase-db supabase-storage supabase-studio supabase-kong redis
   ```

4. **Initialize database**:
   ```bash
   python cli.py migrate
   python cli.py create-user
   ```

5. **Start the application**:
   ```bash
   # Terminal 1: API server
   python cli.py serve --reload

   # Terminal 2: Worker
   python cli.py worker
   ```

## API Documentation

### Authentication

All API endpoints (except health check) require JWT authentication.

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password
```

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "role": "uploader"
}
```

### Document Processing

#### Upload Document
```http
POST /api/v1/jobs
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <pdf_file>
```

#### Get Job Status
```http
GET /api/v1/jobs/{job_id}
Authorization: Bearer <jwt_token>
```

#### Get Processing Results
```http
GET /api/v1/jobs/{job_id}/result
Authorization: Bearer <jwt_token>
```

#### Download Redacted PDF
```http
GET /api/v1/jobs/{job_id}/redacted
Authorization: Bearer <jwt_token>
```

### Human Review

#### Get Review Queue
```http
GET /api/v1/review/queue?limit=20
Authorization: Bearer <jwt_token>
```

#### Review Region
```http
POST /api/v1/review/{region_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "verified_value": "corrected text",
  "action": "correct"
}
```

### Admin Functions

#### Export Training Data
```http
GET /api/v1/export/jsonl?job_id=<job_id>
Authorization: Bearer <admin_jwt_token>
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database (Supabase)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# Redis
REDIS_URL=redis://localhost:6379/0

# Supabase Storage
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_STORAGE_URL=http://localhost:54321/storage/v1
SUPABASE_BUCKET=yantra-docs

# S3/Storage (fallback)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=yantra-ai-docs

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=4320

# Processing
OCR_CONFIDENCE_THRESHOLD=0.6
TRUST_SCORE_THRESHOLD=0.6
MAX_FILE_SIZE_MB=50
WORKER_CONCURRENCY=2
```

### Trust Score Configuration

The trust score is calculated as a weighted average:
- OCR Confidence: 50%
- Translation Confidence: 25%
- PII Detection Confidence: 15%
- Layout Detection Confidence: 10%

Regions with trust scores below the threshold are automatically sent for human review.

## Database Schema

### Core Tables

- **users**: User accounts with role-based access (uploader, reviewer, admin)
- **jobs**: Document processing jobs with status tracking
- **pages**: Individual pages from processed documents
- **regions**: Extracted text regions with confidence scores and metadata
- **audit_logs**: Complete audit trail of all human actions

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Core configuration and utilities
│   ├── crud/             # Database operations
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   └── worker/           # Background job processing
├── alembic/              # Database migrations
├── tests/                # Test suite
├── docker-compose.yml    # Docker configuration
├── requirements.txt      # Python dependencies
└── cli.py               # Command-line interface
```

### CLI Commands

```bash
# Database management
python cli.py init-db
python cli.py migrate
python cli.py create-migration "description"
python cli.py reset-db

# User management
python cli.py create-user
python cli.py list-users

# Development
python cli.py serve --reload
python cli.py worker
```

### Adding New Features

1. **Models**: Add SQLAlchemy models in `app/models/`
2. **Schemas**: Add Pydantic schemas in `app/schemas/`
3. **CRUD**: Add database operations in `app/crud/`
4. **API**: Add endpoints in `app/api/v1/endpoints/`
5. **Services**: Add business logic in `app/services/`
6. **Migrations**: Generate with `python cli.py create-migration`

## Deployment

### Production Considerations

1. **Security**:
   - Use HTTPS in production
   - Configure proper CORS origins
   - Use environment variables for secrets
   - Enable audit logging

2. **Scaling**:
   - Increase worker concurrency based on load
   - Use managed PostgreSQL and Redis services
   - Configure S3 for production storage
   - Set up monitoring and alerting

3. **Monitoring**:
   - Enable Sentry for error tracking
   - Monitor queue depths and processing times
   - Set up health checks and logging
   - Track trust score distributions

### Docker Production Deployment

```bash
# Production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up -d --scale worker=3
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_auth.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the logs in the RQ dashboard

---

**Yantra AI** - Transform documents into structured, trustworthy data.