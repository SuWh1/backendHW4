import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/appdb")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # AWS S3
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_bucket_name: str = os.getenv("AWS_BUCKET_NAME", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Celery
    celery_broker_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    celery_result_backend: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # OpenAI for A2A Voice Communication
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        env_file = ".env"


settings = Settings() 