"""
Deepgram Speech-to-Text integration
Handles real-time audio transcription
"""
import asyncio
from typing import Optional, Callable
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DeepgramSTT:
    """Deepgram Speech-to-Text handler"""
    
    def __init__(self):
        """Initialize Deepgram client"""
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in environment")
        
        config = DeepgramClientOptions(
            api_key=settings.DEEPGRAM_API_KEY
        )
        self.client = DeepgramClient(config)
        self.connection = None
        self.is_connected = False
    
    async def start_streaming(
        self,
        on_transcript: Callable[[str, bool], None],
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Start streaming audio to Deepgram
        
        Args:
            on_transcript: Callback function(transcript, is_final)
            on_error: Error callback function (optional)
        """
        try:
            # Configure live transcription options
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
            )
            
            # Create live transcription connection
            self.connection = self.client.listen.asynclive.v("1")
            
            # Set up event handlers
            async def on_message(self_inner, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) > 0:
                    is_final = result.is_final
                    on_transcript(sentence, is_final)
            
            async def on_error_handler(self_inner, error, **kwargs):
                logger.error(f"Deepgram error: {error}")
                if on_error:
                    on_error(error)
            
            async def on_close(self_inner, close, **kwargs):
                logger.info("Deepgram connection closed")
                self.is_connected = False
            
            # Register event handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.connection.on(LiveTranscriptionEvents.Error, on_error_handler)
            self.connection.on(LiveTranscriptionEvents.Close, on_close)
            
            # Start the connection
            await self.connection.start(options)
            self.is_connected = True
            logger.info("✅ Deepgram connection started")
            
        except Exception as e:
            logger.error(f"Failed to start Deepgram: {e}")
            if on_error:
                on_error(e)
            raise
    
    async def send_audio(self, audio_data: bytes):
        """
        Send audio data to Deepgram for transcription
        
        Args:
            audio_data: Raw audio bytes (PCM format recommended)
        """
        if not self.is_connected or not self.connection:
            raise RuntimeError("Deepgram connection not established")
        
        try:
            await self.connection.send(audio_data)
        except Exception as e:
            logger.error(f"Error sending audio to Deepgram: {e}")
            raise
    
    async def finish(self):
        """Close the Deepgram connection gracefully"""
        if self.connection:
            try:
                await self.connection.finish()
                logger.info("Deepgram connection finished")
            except Exception as e:
                logger.error(f"Error finishing Deepgram connection: {e}")
            finally:
                self.is_connected = False
                self.connection = None
    
    async def close(self):
        """Alias for finish()"""
        await self.finish()


class DeepgramTranscriber:
    """
    Simplified Deepgram transcriber for one-shot audio
    Use this for recorded audio chunks instead of streaming
    """
    
    def __init__(self):
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not set in environment")
        
        config = DeepgramClientOptions(
            api_key=settings.DEEPGRAM_API_KEY
        )
        self.client = DeepgramClient(config)
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        mimetype: str = "audio/wav"
    ) -> str:
        """
        Transcribe audio file or buffer
        
        Args:
            audio_data: Audio file bytes
            mimetype: Audio format (e.g., 'audio/wav', 'audio/mp3')
        
        Returns:
            Transcribed text
        """
        try:
            options = {
                "model": "nova-2",
                "language": "en-US",
                "smart_format": True,
            }
            
            response = await self.client.listen.asyncrest.v("1").transcribe_file(
                {"buffer": audio_data, "mimetype": mimetype},
                options
            )
            
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
