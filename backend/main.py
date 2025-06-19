from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uvicorn
import json
import base64
import asyncio
import logging

from database import get_db, engine, Base
from models import Item, FileUpload, Agent, CommunicationSession, VoiceMessage
from schemas import (
    ItemCreate, ItemUpdate, ItemResponse, FileUploadResponse,
    AgentCreate, AgentUpdate, AgentResponse, CommunicationSessionResponse,
    VoiceMessageResponse, WebSocketMessage, VoiceData, StatusUpdate, ConnectionRequest
)
from redis_client import redis_client
from s3_client import s3_client
from tasks import process_file_upload
from websocket_manager import connection_manager
from openai_service import openai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="A2A Voice Communication System",
    description="Agent-to-Agent Voice-to-Voice communication with OpenAI integration",
    version="2.0.0"
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


# A2A Communication Endpoints

@app.post("/agents/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new agent"""
    # Check if agent_id already exists
    result = await db.execute(select(Agent).where(Agent.agent_id == agent.agent_id))
    existing_agent = result.scalar_one_or_none()
    
    if existing_agent:
        raise HTTPException(status_code=400, detail="Agent ID already exists")
    
    db_agent = Agent(**agent.dict())
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    
    return db_agent


@app.get("/agents/", response_model=List[AgentResponse])
async def get_agents(db: AsyncSession = Depends(get_db)):
    """Get all agents"""
    result = await db.execute(select(Agent))
    agents = result.scalars().all()
    return agents


@app.get("/agents/online", response_model=List[dict])
async def get_online_agents():
    """Get currently online agents"""
    return connection_manager.get_online_agents()


@app.get("/sessions/active", response_model=List[dict])
async def get_active_sessions():
    """Get active communication sessions"""
    return connection_manager.get_active_sessions()


# WebSocket endpoint for A2A communication
@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time A2A voice communication"""
    await connection_manager.connect(websocket, agent_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            message_data = message.get("data", {})
            
            if message_type == "voice_message":
                # Handle voice message
                await handle_voice_message(agent_id, message_data)
            
            elif message_type == "status_update":
                # Handle status update
                status = message_data.get("status")
                await connection_manager.update_agent_status(agent_id, status)
            
            elif message_type == "start_session":
                # Start communication session
                target_id = message_data.get("target_agent_id")
                session_id = await connection_manager.start_communication_session(agent_id, target_id)
                
                if session_id:
                    response = {
                        "type": "session_created",
                        "data": {"session_id": session_id}
                    }
                    await websocket.send_text(json.dumps(response))
            
            elif message_type == "end_session":
                # End communication session
                session_id = message_data.get("session_id")
                await connection_manager.end_communication_session(session_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect(agent_id)
        logger.info(f"Agent {agent_id} disconnected")


async def handle_voice_message(sender_id: str, voice_data: dict):
    """Process voice message through OpenAI and handle response"""
    try:
        # Extract audio data
        audio_base64 = voice_data.get("audio_base64")
        if not audio_base64:
            logger.error("No audio data provided in voice message")
            return
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Update sender status to "thinking"
        await connection_manager.update_agent_status(sender_id, "thinking")
        
        # Process through OpenAI
        ai_result = await openai_service.process_voice_message(audio_bytes)
        
        if ai_result["success"]:
            # Send AI response back to sender
            await connection_manager.handle_ai_response(sender_id, ai_result)
            
            # Update status to "speaking"
            await connection_manager.update_agent_status(sender_id, "speaking")
            
            # After a delay, set back to "online"
            await asyncio.sleep(3)  # Simulate speaking time
            await connection_manager.update_agent_status(sender_id, "online")
        else:
            # Handle error
            error_message = {
                "type": "error",
                "data": {
                    "message": "Failed to process voice message",
                    "timestamp": voice_data.get("timestamp")
                }
            }
            await connection_manager.send_personal_message(error_message, sender_id)
            await connection_manager.update_agent_status(sender_id, "online")
    
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await connection_manager.update_agent_status(sender_id, "online")


# Health Check Endpoints

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "A2A Voice Communication System"}


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


@app.get("/health/openai")
async def openai_health_check():
    """OpenAI integration health check"""
    if openai_service.client:
        return {"status": "healthy", "service": "OpenAI", "message": "API key configured"}
    else:
        return {"status": "unhealthy", "service": "OpenAI", "message": "API key not configured"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

