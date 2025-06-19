import asyncio
import base64
import io
import tempfile
from typing import Optional
import aiofiles
from openai import AsyncOpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured. Voice features will be disabled.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def speech_to_text(self, audio_data: bytes, format: str = "webm") -> Optional[str]:
        """
        Convert speech to text using OpenAI Whisper
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Use OpenAI Whisper for transcription
            with open(temp_file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            logger.info(f"Speech transcribed: {transcript[:100]}...")
            return transcript
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                import os
                os.unlink(temp_file_path)
            except:
                pass
    
    async def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """
        Convert text to speech using OpenAI TTS
        Available voices: alloy, echo, fable, onyx, nova, shimmer
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            # Get the audio content directly
            audio_content = response.content
            
            logger.info(f"Text-to-speech generated for: {text[:50]}...")
            return audio_content
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return None
    
    async def generate_ai_response(self, transcribed_text: str, context: str = "") -> Optional[str]:
        """
        Generate AI response based on transcribed speech
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            # Create a context-aware prompt for A2A communication
            system_prompt = """You are an AI agent in a voice-to-voice communication system. 
            You should respond naturally and conversationally, as if you're having a real-time voice conversation.
            Keep responses concise but friendly. You're designed to assist and communicate effectively with other agents."""
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if context:
                messages.append({"role": "system", "content": f"Context: {context}"})
            
            messages.append({"role": "user", "content": transcribed_text})
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            logger.info(f"AI response generated: {ai_response[:50]}...")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
    
    async def process_voice_message(self, audio_data: bytes, format: str = "webm") -> dict:
        """
        Complete pipeline: Speech -> Text -> AI Response -> Speech
        """
        result = {
            "transcribed_text": None,
            "ai_response_text": None,
            "ai_response_audio": None,
            "success": False
        }
        
        try:
            # Step 1: Speech to Text
            transcribed_text = await self.speech_to_text(audio_data, format)
            if not transcribed_text:
                return result
            
            result["transcribed_text"] = transcribed_text
            
            # Step 2: Generate AI Response
            ai_response_text = await self.generate_ai_response(transcribed_text)
            if not ai_response_text:
                return result
            
            result["ai_response_text"] = ai_response_text
            
            # Step 3: Text to Speech for AI Response
            ai_response_audio = await self.text_to_speech(ai_response_text)
            if not ai_response_audio:
                return result
            
            result["ai_response_audio"] = base64.b64encode(ai_response_audio).decode()
            result["success"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error in voice message processing pipeline: {e}")
            return result


# Global OpenAI service instance
openai_service = OpenAIService() 