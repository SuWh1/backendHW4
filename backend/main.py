from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uvicorn

from database import get_db, engine, Base
from models import Item, FileUpload
from schemas import ItemCreate, ItemUpdate, ItemResponse, FileUploadResponse
from redis_client import redis_client
from s3_client import s3_client
from tasks import process_file_upload

app = FastAPI(
    title="Production FastAPI App",
    description="A production-ready FastAPI application with PostgreSQL, Redis, Celery, and S3",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# CRUD Endpoints for Items

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    """Create a new item"""
    db_item = Item(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    
    # Clear cache for items list
    await redis_client.clear_pattern("items:*")
    
    return db_item


@app.get("/items/", response_model=List[ItemResponse])
async def get_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all items with Redis caching"""
    cache_key = f"items:skip:{skip}:limit:{limit}"
    
    # Try to get from cache first
    cached_items = await redis_client.get(cache_key)
    if cached_items:
        return cached_items
    
    # If not in cache, get from database
    result = await db.execute(select(Item).offset(skip).limit(limit))
    items = result.scalars().all()
    
    # Convert to response models
    items_response = [ItemResponse.from_orm(item) for item in items]
    
    # Cache the result
    await redis_client.set(cache_key, items_response, expire=300)
    
    return items_response


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific item with Redis caching"""
    cache_key = f"item:{item_id}"
    
    # Try to get from cache first
    cached_item = await redis_client.get(cache_key)
    if cached_item:
        return cached_item
    
    # If not in cache, get from database
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_response = ItemResponse.from_orm(item)
    
    # Cache the result
    await redis_client.set(cache_key, item_response, expire=300)
    
    return item_response


@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item_update: ItemUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing item"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    db_item = result.scalar_one_or_none()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update fields
    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    await db.commit()
    await db.refresh(db_item)
    
    # Clear cache
    await redis_client.delete(f"item:{item_id}")
    await redis_client.clear_pattern("items:*")
    
    return db_item


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an item"""
    result = await db.execute(select(Item).where(Item.id == item_id))
    db_item = result.scalar_one_or_none()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(db_item)
    await db.commit()
    
    # Clear cache
    await redis_client.delete(f"item:{item_id}")
    await redis_client.clear_pattern("items:*")
    
    return {"message": "Item deleted successfully"}


# File Upload Endpoints

@app.post("/upload/", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Upload file to S3 and save metadata to database"""
    
    # Read file content
    file_content = await file.read()
    
    # Upload to S3
    upload_result = await s3_client.upload_file(
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type
    )
    
    if not upload_result:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")
    
    # Save metadata to database
    db_file = FileUpload(
        filename=upload_result['filename'],
        s3_key=upload_result['s3_key'],
        s3_url=upload_result['s3_url'],
        content_type=upload_result['content_type'],
        file_size=upload_result['file_size']
    )
    
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    
    # Trigger background task for file processing
    process_file_upload.delay({
        'file_id': db_file.id,
        'filename': db_file.filename,
        's3_key': db_file.s3_key
    })
    
    return db_file


@app.get("/files/", response_model=List[FileUploadResponse])
async def get_uploaded_files(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all uploaded files"""
    result = await db.execute(select(FileUpload).offset(skip).limit(limit))
    files = result.scalars().all()
    return files


@app.get("/files/{file_id}", response_model=FileUploadResponse)
async def get_uploaded_file(file_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific uploaded file metadata"""
    result = await db.execute(select(FileUpload).where(FileUpload.id == file_id))
    file_upload = result.scalar_one_or_none()
    
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file_upload


@app.delete("/files/{file_id}")
async def delete_uploaded_file(file_id: int, db: AsyncSession = Depends(get_db)):
    """Delete uploaded file from S3 and database"""
    result = await db.execute(select(FileUpload).where(FileUpload.id == file_id))
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from S3
    await s3_client.delete_file(db_file.s3_key)
    
    # Delete from database
    await db.delete(db_file)
    await db.commit()
    
    return {"message": "File deleted successfully"}


# Health Check Endpoints

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "FastAPI App"}


@app.get("/health/redis")
async def redis_health_check():
    """Redis health check"""
    try:
        await redis_client.set("health_check", "ok", expire=60)
        result = await redis_client.get("health_check")
        if result == "ok":
            return {"status": "healthy", "service": "Redis"}
        else:
            return {"status": "unhealthy", "service": "Redis"}
    except Exception as e:
        return {"status": "unhealthy", "service": "Redis", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

