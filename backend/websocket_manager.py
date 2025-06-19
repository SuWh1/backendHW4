import json
import logging
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Store active connections by agent_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store agent statuses
        self.agent_statuses: Dict[str, str] = {}
        # Store active communication sessions
        self.active_sessions: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str):
        """Accept a new WebSocket connection for an agent"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.agent_statuses[agent_id] = "online"
        
        logger.info(f"Agent {agent_id} connected")
        
        # Notify other agents about the new connection
        await self.broadcast_status_update(agent_id, "online")
    
    def disconnect(self, agent_id: str):
        """Remove an agent's connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        
        if agent_id in self.agent_statuses:
            del self.agent_statuses[agent_id]
        
        logger.info(f"Agent {agent_id} disconnected")
    
    async def send_personal_message(self, message: dict, agent_id: str):
        """Send a message to a specific agent"""
        if agent_id in self.active_connections:
            try:
                websocket = self.active_connections[agent_id]
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Error sending message to {agent_id}: {e}")
                # Remove disconnected client
                self.disconnect(agent_id)
                return False
        return False
    
    async def broadcast_message(self, message: dict, exclude_agent: Optional[str] = None):
        """Broadcast a message to all connected agents"""
        disconnected_agents = []
        
        for agent_id, websocket in self.active_connections.items():
            if exclude_agent and agent_id == exclude_agent:
                continue
            
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {agent_id}: {e}")
                disconnected_agents.append(agent_id)
        
        # Clean up disconnected agents
        for agent_id in disconnected_agents:
            self.disconnect(agent_id)
    
    async def broadcast_status_update(self, agent_id: str, status: str):
        """Broadcast agent status update to all connected agents"""
        message = {
            "type": "status_update",
            "data": {
                "agent_id": agent_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.broadcast_message(message, exclude_agent=agent_id)
    
    async def update_agent_status(self, agent_id: str, status: str):
        """Update and broadcast agent status"""
        self.agent_statuses[agent_id] = status
        await self.broadcast_status_update(agent_id, status)
    
    async def start_communication_session(self, initiator_id: str, target_id: str) -> Optional[str]:
        """Start a communication session between two agents"""
        if target_id not in self.active_connections:
            return None
        
        session_id = f"session_{initiator_id}_{target_id}_{int(datetime.now().timestamp())}"
        
        session_data = {
            "session_id": session_id,
            "initiator_id": initiator_id,
            "target_id": target_id,
            "status": "active",
            "started_at": datetime.now().isoformat()
        }
        
        self.active_sessions[session_id] = session_data
        
        # Notify both agents about the session
        session_message = {
            "type": "session_started",
            "data": session_data
        }
        
        await self.send_personal_message(session_message, initiator_id)
        await self.send_personal_message(session_message, target_id)
        
        logger.info(f"Communication session {session_id} started between {initiator_id} and {target_id}")
        return session_id
    
    async def end_communication_session(self, session_id: str):
        """End a communication session"""
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            session_data["status"] = "ended"
            session_data["ended_at"] = datetime.now().isoformat()
            
            # Notify agents about session end
            end_message = {
                "type": "session_ended",
                "data": session_data
            }
            
            await self.send_personal_message(end_message, session_data["initiator_id"])
            await self.send_personal_message(end_message, session_data["target_id"])
            
            del self.active_sessions[session_id]
            logger.info(f"Communication session {session_id} ended")
    
    async def handle_voice_message(self, sender_id: str, voice_data: dict):
        """Handle incoming voice message and forward to appropriate recipient"""
        receiver_id = voice_data.get("receiver_id")
        session_id = voice_data.get("session_id")
        
        if not receiver_id or receiver_id not in self.active_connections:
            logger.warning(f"Cannot deliver voice message: receiver {receiver_id} not connected")
            return False
        
        # Update sender status to "thinking" (AI processing)
        await self.update_agent_status(sender_id, "thinking")
        
        # Forward voice message to receiver
        message = {
            "type": "voice_message",
            "data": {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "session_id": session_id,
                "audio_base64": voice_data.get("audio_base64"),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        success = await self.send_personal_message(message, receiver_id)
        
        if success:
            logger.info(f"Voice message forwarded from {sender_id} to {receiver_id}")
        
        return success
    
    async def handle_ai_response(self, original_sender_id: str, ai_response_data: dict):
        """Handle AI response and send back to original sender"""
        message = {
            "type": "ai_response",
            "data": {
                "original_sender_id": original_sender_id,
                "transcribed_text": ai_response_data.get("transcribed_text"),
                "ai_response_text": ai_response_data.get("ai_response_text"),
                "ai_response_audio": ai_response_data.get("ai_response_audio"),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        success = await self.send_personal_message(message, original_sender_id)
        
        if success:
            logger.info(f"AI response sent to {original_sender_id}")
        
        return success
    
    def get_online_agents(self) -> List[Dict]:
        """Get list of all online agents"""
        return [
            {
                "agent_id": agent_id,
                "status": self.agent_statuses.get(agent_id, "unknown")
            }
            for agent_id in self.active_connections.keys()
        ]
    
    def get_active_sessions(self) -> List[Dict]:
        """Get list of active communication sessions"""
        return list(self.active_sessions.values())


# Global connection manager instance
connection_manager = ConnectionManager() 