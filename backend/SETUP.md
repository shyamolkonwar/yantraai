# Yantra AI Backend Setup Guide

This guide will help you set up the Yantra AI backend with Supabase local development environment.

## Prerequisites

- Docker and Docker Compose
- Git
- (Optional) Python 3.11+ for local development

## Quick Setup

### 1. Clone and Start Services

```bash
# Clone the repository
git clone <repository-url>
cd yantra-ai/backend

# Start all Supabase services
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
```

### 2. Initialize Supabase Storage

```bash
# Create required storage buckets
docker-compose exec web python scripts/init_supabase.py
```

### 3. Initialize Database

```bash
# Run database migrations
docker-compose exec web python cli.py migrate

# Create admin user
docker-compose exec web python cli.py create-user
```

### 4. Verify Setup

Access the following URLs to verify everything is working:

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Supabase Studio**: http://localhost:54323
- **Supabase API**: http://localhost:54321
- **RQ Dashboard**: http://localhost:9181

## Service Details

### Supabase Services

| Service | Port | Purpose |
|---------|------|---------|
| Supabase DB | 54322 | PostgreSQL database |
| Supabase Studio | 54323 | Admin interface |
| Kong Gateway | 54321 | API gateway |
| Storage API | 54327 | File storage |
| Auth Service | 54326 | Authentication |
| REST API | 54328 | Database REST API |

### Application Services

| Service | Port | Purpose |
|---------|------|---------|
| FastAPI Web Server | 8000 | Main application API |
| RQ Worker | - | Background job processing |
| RQ Dashboard | 9181 | Job queue monitoring |
| Redis | 6379 | Job queue backend |

## Default Credentials

### Supabase
- **Database**: `postgres/postgres@localhost:54322/postgres`
- **Studio**: No auth required for local
- **Anon Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0`
- **Service Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU`

### Storage Buckets
- **yantra-docs**: Private bucket for document storage
- **yantra-public**: Public bucket for assets (optional)

## Development Workflow

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Initialize (first time only)
```bash
docker-compose exec web python scripts/init_supabase.py
docker-compose exec web python cli.py migrate
docker-compose exec web python cli.py create-user
```

### 3. Develop
- Web server auto-reloads on code changes
- Workers will process queued jobs
- Use Supabase Studio to inspect data

### 4. Test API
```bash
# Health check
curl http://localhost:8000/health

# Upload a document (after login)
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@test.pdf"
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check logs
   docker-compose logs supabase-db
   docker-compose logs web
   ```

2. **Database connection issues**
   - Wait 30-60 seconds after `docker-compose up`
   - Check if port 54322 is available

3. **Storage bucket creation fails**
   ```bash
   # Retry initialization
   docker-compose exec web python scripts/init_supabase.py
   ```

4. **API returning 500 errors**
   ```bash
   # Check application logs
   docker-compose logs web

   # Check if database migrations ran
   docker-compose exec web python cli.py migrate
   ```

### Reset Everything

```bash
# Stop and remove all containers
docker-compose down -v

# Restart
docker-compose up -d

# Re-initialize
docker-compose exec web python scripts/init_supabase.py
docker-compose exec web python cli.py migrate
```

## Local Development

For advanced local development, you can run the Python application directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment
cp .env.example .env

# Start only database services
docker-compose up -d supabase-db redis

# Run migrations
python cli.py migrate

# Start web server
python cli.py serve --reload

# Start worker (in another terminal)
python cli.py worker
```

## Production Considerations

When deploying to production:

1. **Security**: Replace all default keys and secrets
2. **Database**: Use managed Supabase project instead of local
3. **Storage**: Configure proper access policies
4. **Monitoring**: Set up logging and alerting
5. **Scaling**: Configure appropriate resource limits

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Upload Documents**: Test with a sample PDF
3. **Check Results**: Monitor processing in RQ Dashboard
4. **Review Data**: Use Supabase Studio to inspect results

## Support

- Check container logs: `docker-compose logs [service-name]`
- API documentation: http://localhost:8000/docs
- Supabase Studio: http://localhost:54323

---

**Happy Coding! 🚀**