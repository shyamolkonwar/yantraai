# Yantra AI - Document Processing & OCR System

Transform messy Indian documents (scanned PDFs, phone photos) into structured JSON with field-level trust scores, PII redaction, and human-in-the-loop review capabilities.

## 🚀 Features

- **AI-Powered OCR**: Extract text from scanned documents using EasyOCR with English and Hindi support
- **PII Detection & Redaction**: Automatically detect and irreversibly redact sensitive information (Aadhaar, PAN, phone numbers, etc.)
- **Trust Scoring**: Calculate confidence scores for each extracted field based on OCR quality, normalization, and PII detection
- **Human-in-the-Loop Review**: Review low-confidence fields and correct them with audit logging
- **Local Processing**: No cloud dependencies - everything runs locally on your machine
- **Modern Web UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- **Role-Based Access**: Support for uploaders, reviewers, and administrators

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Pydantic schemas
- **OCR Engine**: EasyOCR (English + Hindi)
- **PII Detection**: Microsoft Presidio Analyzer
- **Storage**: Local filesystem (`./backend/data/jobs/`)
- **Processing**: Synchronous pipeline with optional Redis RQ async workers
- **APIs**: RESTful endpoints for job management, review queue, and health checks

### Frontend (Next.js)
- **Framework**: Next.js 16 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for auth, TanStack Query for server state
- **Authentication**: Supabase Auth
- **UI Components**: Custom component library with Radix UI primitives
- **PDF Viewing**: React-PDF for document visualization

### Data Flow
1. **Upload**: User uploads PDF/image via web interface
2. **Processing**: Backend converts to images, runs OCR, detects PII, calculates trust scores
3. **Redaction**: Creates irreversibly redacted PDF with PII masked
4. **Review**: Low-trust fields flagged for human review and correction
5. **Export**: Structured JSON and redacted PDF available for download

## 📋 Prerequisites

### System Requirements
- **Python**: 3.10 or 3.11
- **Node.js**: 18+ with npm/pnpm
- **System Dependencies** (Ubuntu/Debian):
  ```bash
  sudo apt-get update
  sudo apt-get install -y poppler-utils build-essential ghostscript python3-dev
  ```

### Optional (for GPU acceleration)
- CUDA-compatible GPU for faster OCR processing
- PyTorch with CUDA support

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd yantra-ai-mvp
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### Environment Configuration
```bash
cp .env.example .env
# Edit .env with your settings (Redis URL, etc.)
```

#### Create Data Directories
```bash
mkdir -p data/jobs
```

#### Start Backend Server
```bash
# Synchronous mode (recommended for development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Async mode with Redis (requires Docker)
docker run -d -p 6379:6379 redis:7-alpine
docker-compose up -d redis
rq worker truth-layer-queue &
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
# or
pnpm install
```

#### Environment Configuration
```bash
cp .env.local.example .env.local
# Configure Supabase credentials and API URL
```

#### Start Development Server
```bash
npm run dev
# or
pnpm dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🚀 Usage

### 1. Authentication
- Visit http://localhost:3000/login
- Sign up or log in with your credentials
- Roles: `uploader`, `reviewer`, `admin`

### 2. Upload Document
- Go to Dashboard
- Drag & drop or click to upload PDF/image
- Wait for processing to complete

### 3. Review Results
- View extracted fields with trust scores
- Review low-confidence fields (< 0.6 trust score)
- Correct errors and submit changes
- Download structured JSON or redacted PDF

### 4. CLI Processing (Optional)
```bash
cd backend
python scripts/process_single.py path/to/document.pdf
```

## 📊 API Endpoints

### Jobs
- `POST /api/v1/jobs` - Upload and process document
- `GET /api/v1/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs/{job_id}/result` - Download JSON results
- `GET /api/v1/jobs/{job_id}/redacted` - Download redacted PDF

### Review
- `GET /api/v1/review/queue` - Get fields needing review
- `POST /api/v1/review/{job_id}/{region_id}` - Submit corrections

### Health
- `GET /api/v1/health` - Service health check

## 🐳 Docker Deployment

### Full Stack with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Or run specific services
docker-compose up backend frontend redis
```

### Individual Services
```bash
# Backend only
cd backend
docker build -t yantra-backend .
docker run -p 8000:8000 -v $(pwd)/data:/app/data yantra-backend

# Frontend only
cd frontend
docker build -t yantra-frontend .
docker run -p 3000:3000 yantra-frontend
```

## 🔧 Configuration

### Backend Environment Variables
```bash
# .env
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png
```

### Frontend Environment Variables
```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📈 Processing Pipeline

1. **Document Ingestion**: Convert PDF to high-res images (300 DPI)
2. **OCR**: Extract text using EasyOCR with confidence scores
3. **Text Normalization**: Clean and standardize extracted text
4. **PII Detection**: Identify sensitive information using Presidio
5. **Trust Scoring**: Calculate field confidence (OCR + normalization + PII)
6. **Redaction**: Create irreversibly masked PDF
7. **Review Queue**: Flag low-trust fields for human correction

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### Manual Testing
```bash
# Process sample document
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -F "file=@testing/sample.pdf"

# Check health
curl http://localhost:8000/api/v1/health
```

## 📊 Monitoring & Metrics

- **Job Processing Stats**: Jobs processed, failed, average trust scores
- **PII Detection Rate**: Percentage of documents with PII detected
- **Review Rate**: Fields requiring human review
- **Performance**: Processing time per document

Metrics are logged to `./backend/data/metrics.log` in JSONL format.

## 🔒 Security & Privacy

- **PII Handling**: Detected PII is irreversibly redacted in PDFs
- **Audit Logging**: All corrections logged with timestamps and user info
- **Local Storage**: No data sent to external services
- **Access Control**: Role-based permissions for different user types

## 🚀 Production Deployment

### Backend
```bash
# Use production ASGI server
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
npm run build
npm start
```

### Reverse Proxy (nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**OCR Quality Poor**
- Ensure high-resolution scans (300+ DPI)
- Check document orientation and skew
- Try different lighting conditions

**PII Not Detected**
- Verify document contains standard PII patterns
- Check language settings (English vs Hindi)
- Review Presidio configuration

**Processing Slow**
- Install PyTorch with CUDA support
- Reduce image DPI for faster processing
- Use async mode with Redis workers

**Frontend Build Errors**
- Clear node_modules and reinstall
- Check Node.js version compatibility
- Verify environment variables

### Logs & Debugging
```bash
# Backend logs
tail -f backend/app.log

# Frontend logs
# Check browser console and terminal output

# Docker logs
docker-compose logs -f backend
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [Microsoft Presidio](https://microsoft.github.io/presidio/)
- [Supabase Auth](https://supabase.com/docs/guides/auth)

---

Built with ❤️ for transforming document processing workflows.
