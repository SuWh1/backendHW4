from celery import Celery
from config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize Celery
celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'tasks.cleanup_old_files',
        'schedule': 3600.0,  # Run every hour
    },
    'health-check': {
        'task': 'tasks.health_check',
        'schedule': 300.0,  # Run every 5 minutes
    },
}


@celery_app.task
def process_file_upload(file_info: dict):
    """Background task to process uploaded files"""
    print(f"Processing file upload: {file_info}")
    # Add your file processing logic here
    # For example: image resizing, virus scanning, etc.
    return {"status": "processed", "file_info": file_info}


@celery_app.task
def send_notification(email: str, subject: str, message: str):
    """Background task to send email notifications"""
    print(f"Sending notification to {email}: {subject}")
    # Add your email sending logic here
    return {"status": "sent", "email": email}


@celery_app.task
def cleanup_old_files():
    """Periodic task to cleanup old files"""
    print("Running cleanup task for old files")
    # Add your cleanup logic here
    return {"status": "completed", "cleaned_files": 0}


@celery_app.task
def health_check():
    """Periodic health check task"""
    print("Running health check")
    # Add your health check logic here
    return {"status": "healthy", "timestamp": str(celery_app.now())} 