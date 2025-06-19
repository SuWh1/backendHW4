from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    s3_key: str
    s3_url: str
    content_type: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# A2A Communication Schemas
class AgentCreate(BaseModel):
    agent_id: str
    name: str


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    id: int
    agent_id: str
    name: str
    status: str
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommunicationSessionCreate(BaseModel):
    session_id: str
    agent_id: str


class CommunicationSessionResponse(BaseModel):
    id: int
    session_id: str
    partner_agent_id: Optional[str] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VoiceMessageCreate(BaseModel):
    session_id: str
    sender_agent_id: str
    receiver_agent_id: str
    transcribed_text: Optional[str] = None


class VoiceMessageResponse(BaseModel):
    id: int
    sender_agent_id: str
    receiver_agent_id: str
    transcribed_text: Optional[str] = None
    response_text: Optional[str] = None
    is_ai_response: bool
    processing_status: str
    audio_duration: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# WebSocket Message Schemas
class WebSocketMessage(BaseModel):
    type: str  # voice_message, status_update, connection, etc.
    data: dict


class VoiceData(BaseModel):
    audio_base64: str  # Base64 encoded audio data
    sender_id: str
    receiver_id: str
    session_id: str


class StatusUpdate(BaseModel):
    agent_id: str
    status: str  # recording, thinking, speaking, idle
    timestamp: datetime


class ConnectionRequest(BaseModel):
    agent_id: str
    target_agent_id: Optional[str] = None 