from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    s3_url = Column(String(1000), nullable=False)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# A2A Communication Models
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="offline")  # offline, online, recording, thinking, speaking
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to sessions
    sessions = relationship("CommunicationSession", back_populates="agent")


class CommunicationSession(Base):
    __tablename__ = "communication_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    partner_agent_id = Column(String(100), nullable=True)  # Connected agent
    status = Column(String(50), default="waiting")  # waiting, active, ended
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="sessions")
    voice_messages = relationship("VoiceMessage", back_populates="session")


class VoiceMessage(Base):
    __tablename__ = "voice_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("communication_sessions.id"), nullable=False)
    sender_agent_id = Column(String(100), nullable=False)
    receiver_agent_id = Column(String(100), nullable=False)
    
    # Voice data
    audio_data = Column(LargeBinary, nullable=True)  # Store small audio files
    audio_s3_key = Column(String(500), nullable=True)  # Or store in S3 for larger files
    audio_duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Transcription
    transcribed_text = Column(Text, nullable=True)
    
    # Response data (if this is a response from OpenAI)
    response_text = Column(Text, nullable=True)
    is_ai_response = Column(Boolean, default=False)
    
    # Status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    session = relationship("CommunicationSession", back_populates="voice_messages") 