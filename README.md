# Production FastAPI App with Docker

A production-ready FastAPI application with PostgreSQL, Redis, Celery, and AWS S3 integration.

## Features

- **FastAPI** with async/await support
- **PostgreSQL** database with SQLAlchemy async ORM
- **Redis** for caching and Celery broker
- **Celery** for background tasks and scheduled jobs
- **AWS S3** integration for file uploads
- **Docker** containers for all services
- **Alembic** for database migrations
- **Health checks** for all services

## Quick Start

1. **Clone and setup environment**:
```bash
git clone <repository>
cd backendHW4
cp .env.example .env
# Edit .env with your AWS credentials and other settings
```

2. **Start all services**:
```bash
docker-compose up --build
```

3. **The application will be available at**:
- FastAPI app: http://localhost:8000
- FastAPI docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
POSTGRES_DB=appdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_BUCKET_NAME=your-s3-bucket-name
AWS_REGION=us-east-1

# Redis Configuration
REDIS_URL=redis://redis:6379

# Database URL
DATABASE_URL=postgresql://postgres:password@db:5432/appdb
```

## API Endpoints

### Items (CRUD with Redis Caching)

- `POST /items/` - Create new item
- `GET /items/` - Get all items (cached)
- `GET /items/{item_id}` - Get specific item (cached)
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

### File Upload (S3 Integration)

- `POST /upload/` - Upload file to S3
- `GET /files/` - Get all uploaded files
- `GET /files/{file_id}` - Get specific file metadata
- `DELETE /files/{file_id}` - Delete file from S3 and database

### Health Checks

- `GET /health` - Basic health check
- `GET /health/redis` - Redis connectivity check

## Development

### Local Development (without Docker)

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Start PostgreSQL and Redis locally**

3. **Run database migrations**:
```bash
alembic upgrade head
```

4. **Start the application**:
```bash
uvicorn main:app --reload
```

5. **Start Celery worker (separate terminal)**:
```bash
celery -A tasks.celery_app worker --loglevel=info
```

6. **Start Celery beat (separate terminal)**:
```bash
celery -A tasks.celery_app beat --loglevel=info
```

### Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

### Monitoring Celery

Monitor Celery tasks with Flower (optional):
```bash
pip install flower
celery -A tasks.celery_app flower
```

## Production Deployment

1. **Security considerations**:
   - Set strong passwords for PostgreSQL
   - Configure CORS origins properly
   - Use environment-specific configurations
   - Enable HTTPS/SSL termination

2. **Scaling**:
   - Use multiple Celery workers
   - Implement database connection pooling
   - Add load balancing for multiple app instances

3. **Monitoring**:
   - Add logging and monitoring services
   - Implement metrics collection
   - Set up alerts for critical services

## Project Structure

```
backend/
├── alembic/                 # Database migrations
├── main.py                  # FastAPI application
├── config.py                # Configuration settings
├── database.py              # Database connection
├── models.py                # SQLAlchemy models
├── schemas.py               # Pydantic schemas
├── redis_client.py          # Redis client
├── s3_client.py             # AWS S3 client
├── tasks.py                 # Celery tasks
└── requirements.txt         # Python dependencies
```

## Testing

The application includes health check endpoints that can be used for monitoring:

```bash
# Test basic health
curl http://localhost:8000/health

# Test Redis connectivity
curl http://localhost:8000/health/redis

# Test item creation
curl -X POST "http://localhost:8000/items/" \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Item", "description": "Test Description"}'

# Test file upload
curl -X POST "http://localhost:8000/upload/" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/file.txt"
``` 