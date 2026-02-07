"""
Audio stream handler for processing incoming audio from browser
"""
import asyncio
import logging
from typing import Optional, Callable
import base64

logger = logging.getLogger(__name__)


class AudioStreamHandler:
    """Handles audio stream from browser microphone"""
    
    def __init__(self):
        self.is_active = False
        self.buffer = bytearray()
        self.sample_rate = 16000  # 16kHz for Deepgram
        self.channels = 1  # Mono
    
    def process_audio_chunk(self, audio_data: bytes) -> bytes:
        """
        Process incoming audio chunk
        
        Args:
            audio_data: Raw audio bytes from browser
        
        Returns:
            Processed audio ready for Deepgram
        """
        # Add to buffer
        self.buffer.extend(audio_data)
        
        # Return processable chunk
        if len(self.buffer) >= 3200:  # ~200ms at 16kHz
            chunk = bytes(self.buffer[:3200])
            self.buffer = self.buffer[3200:]
            return chunk
        
        return b""
    
    def decode_base64_audio(self, base64_audio: str) -> bytes:
        """
        Decode base64 encoded audio from browser
        
        Args:
            base64_audio: Base64 encoded audio string
        
        Returns:
            Decoded audio bytes
        """
        try:
            return base64.b64decode(base64_audio)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            raise
    
    def clear_buffer(self):
        """Clear audio buffer"""
        self.buffer = bytearray()
    
    def get_buffer_size(self) -> int:
        """Get current buffer size in bytes"""
        return len(self.buffer)


class WebSocketAudioHandler:
    """
    WebSocket handler for real-time audio streaming
    Coordinates between browser audio and Deepgram
    """
    
    def __init__(
        self,
        on_transcript: Callable[[str, bool], None],
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Initialize WebSocket audio handler
        
        Args:
            on_transcript: Callback for transcription results
            on_error: Error callback (optional)
        """
        self.on_transcript = on_transcript
        self.on_error = on_error
        self.audio_handler = AudioStreamHandler()
        self.deepgram_stt = None
        self.is_streaming = False
    
    async def start(self):
        """Start audio streaming session"""
        from app.voice.deepgram import DeepgramSTT
        
        try:
            self.deepgram_stt = DeepgramSTT()
            await self.deepgram_stt.start_streaming(
                on_transcript=self.on_transcript,
                on_error=self.on_error
            )
            self.is_streaming = True
            logger.info("Audio streaming started")
            
        except Exception as e:
            logger.error(f"Failed to start audio streaming: {e}")
            if self.on_error:
                self.on_error(e)
            raise
    
    async def process_audio_data(self, audio_data: str | bytes):
        """
        Process incoming audio data from WebSocket
        
        Args:
            audio_data: Audio data (base64 string or bytes)
        """
        if not self.is_streaming:
            raise RuntimeError("Audio streaming not started")
        
        try:
            # Decode if base64 string
            if isinstance(audio_data, str):
                audio_bytes = self.audio_handler.decode_base64_audio(audio_data)
            else:
                audio_bytes = audio_data
            
            # Process chunk
            chunk = self.audio_handler.process_audio_chunk(audio_bytes)
            
            # Send to Deepgram if chunk is ready
            if chunk:
                await self.deepgram_stt.send_audio(chunk)
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            if self.on_error:
                self.on_error(e)
    
    async def stop(self):
        """Stop audio streaming session"""
        self.is_streaming = False
        
        if self.deepgram_stt:
            await self.deepgram_stt.finish()
        
        self.audio_handler.clear_buffer()
        logger.info("Audio streaming stopped")
