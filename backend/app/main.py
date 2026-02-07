"""
Main FastAPI application for NEXUS AI
Orchestrates voice input, intent detection, and service execution
"""
from fastapi import FastAPI, WebSocket, Depends, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.config import settings
from app.database import get_db, init_db
from app.models import ServiceCredentials, ConversationMemory
from app.memory.manager import MemoryManager
from app.intent.detector import IntentDetector, Intent, ActionType
from app.intent.entity_resolver import EntityResolver
from app.voice.deepgram import DeepgramTranscriber
from app.services.gmail import GmailService
from app.services.maps import GoogleMapsService
from app.services.spotify import SpotifyService
from app.workflows.n8n_trigger import N8nWorkflowTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Voice-First Intelligent Automation Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
intent_detector = IntentDetector()
deepgram_transcriber = DeepgramTranscriber()
n8n_trigger = N8nWorkflowTrigger()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("🚀 NEXUS AI Backend Started")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NEXUS AI - Voice-First Automation Platform",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NEXUS AI"}


@app.post("/api/voice/process")
async def process_voice_command(
    audio_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Process voice command from audio data
    
    Expected payload:
    {
        "audio": "base64_encoded_audio",
        "format": "audio/wav"
    }
    """
    try:
        # Decode and transcribe audio
        import base64
        audio_bytes = base64.b64decode(audio_data["audio"])
        
        transcript = await deepgram_transcriber.transcribe_audio(
            audio_bytes,
            mimetype=audio_data.get("format", "audio/wav")
        )
        
        if not transcript:
            return {"error": "Could not transcribe audio"}
        
        logger.info(f"Transcribed: {transcript}")
        
        # Process the transcript
        result = await process_text_command(transcript, db)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/text/process")
async def process_text_command(
    command: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process text command (for testing or text input)
    
    Main intelligence orchestration happens here
    """
    try:
        # Initialize memory manager
        memory = MemoryManager(db)
        entity_resolver = EntityResolver(memory)
        
        # 1. Detect intent
        intent, action_type = intent_detector.detect(command)
        
        logger.info(f"Intent: {intent}, Action: {action_type}")
        
        # 2. Extract parameters
        params = intent_detector.extract_parameters(intent, command)
        
        # 3. Resolve entities using memory
        entities = entity_resolver.resolve_entities(command, intent, params)
        
        # 4. Check if clarification needed
        if entity_resolver.needs_clarification(entities):
            clarification = entity_resolver.generate_clarification_options(
                entities.get("reference_type", "general")
            )
            return {
                "type": "clarification",
                "question": clarification["question"],
                "options": clarification["options"]
            }
        
        # 5. Execute action based on intent
        result = await execute_intent(
            intent,
            action_type,
            entities,
            db
        )
        
        # 6. Store interaction in memory
        memory.store_interaction(
            user_input=command,
            intent=intent,
            entities=entities,
            action_taken=action_type,
            result_summary=result.get("voice_response", "")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return {
            "type": "error",
            "message": str(e),
            "voice_response": "Sorry, I encountered an error processing your request."
        }


async def execute_intent(
    intent: Intent,
    action_type: ActionType,
    entities: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    Execute the detected intent
    
    Routes to appropriate service or UI handoff
    """
    memory = MemoryManager(db)
    
    # UI Handoff actions
    if action_type == ActionType.UI_HANDOFF:
        return handle_ui_handoff(intent, entities, memory)
    
    # API actions
    if action_type == ActionType.API:
        return await handle_api_action(intent, entities, db, memory)
    
    return {
        "type": "error",
        "message": "Unknown action type",
        "voice_response": "I'm not sure how to handle that request."
    }


def handle_ui_handoff(
    intent: Intent,
    entities: Dict[str, Any],
    memory: MemoryManager
) -> Dict[str, Any]:
    """Handle UI handoff intents"""
    
    if intent == Intent.GMAIL_OPEN_UI:
        url = GmailService.generate_gmail_url()
        return {
            "type": "ui_handoff",
            "action": "open_url",
            "url": url,
            "voice_response": "Opening Gmail for you now."
        }
    
    elif intent == Intent.MAPS_DIRECTIONS:
        destination = entities.get("destination")
        
        # Resolve destination from memory if not provided
        if not destination:
            loc_ref = memory.get_last_reference("location", limit=1)
            if loc_ref:
                destination = loc_ref[0].ref_name
        
        if not destination:
            return {
                "type": "clarification",
                "question": "Where would you like directions to?",
                "voice_response": "Where would you like directions to?"
            }
        
        url = GoogleMapsService.generate_directions_url("Current Location", destination)
        
        # Store location reference
        memory.store_context_reference("location", destination, destination)
        
        return {
            "type": "ui_handoff",
            "action": "open_url",
            "url": url,
            "voice_response": f"Opening directions to {destination}."
        }
    
    elif intent == Intent.SPOTIFY_OPEN_UI:
        url = SpotifyService.generate_spotify_url()
        return {
            "type": "ui_handoff",
            "action": "open_url",
            "url": url,
            "voice_response": "Opening Spotify for you."
        }
    
    return {
        "type": "error",
        "voice_response": "I couldn't open that for you."
    }


async def handle_api_action(
    intent: Intent,
    entities: Dict[str, Any],
    db: Session,
    memory: MemoryManager
) -> Dict[str, Any]:
    """Handle API-based actions"""
    
    # Get service credentials
    creds = get_service_credentials(db)
    
    # Gmail actions
    if intent == Intent.GMAIL_SUMMARIZE:
        if "gmail" not in creds:
            return {
                "type": "error",
                "voice_response": "Gmail is not connected. Please connect your Gmail account first."
            }
        
        # Use n8n workflow
        result = await n8n_trigger.gmail_summarize(
            access_token=creds["gmail"]["access_token"],
            max_results=10
        )
        
        if result["status"] == "success" and result["data"]:
            data = result["data"]
            
            # Store email references
            for email in data.get("emails", [])[:5]:
                memory.store_context_reference(
                    "email",
                    email["id"],
                    f"{email['subject']} from {email['from'].split('<')[0].strip()}",
                    {"from": email["from"], "subject": email["subject"]}
                )
            
            return {
                "type": "api_response",
                "data": data,
                "voice_response": data.get("text_summary", "You have no new emails.")
            }
    
    elif intent == Intent.GMAIL_REPLY:
        if "gmail" not in creds:
            return {
                "type": "error",
                "voice_response": "Gmail is not connected."
            }
        
        # Resolve email reference
        email_ref = entities.get("resolved_reference")
        if not email_ref:
            return {
                "type": "clarification",
                "question": "Which email would you like to reply to?",
                "voice_response": "Which email would you like to reply to?"
            }
        
        reply_content = entities.get("reply_content")
        if not reply_content:
            return {
                "type": "clarification",
                "question": "What would you like to say in your reply?",
                "voice_response": "What would you like to say?"
            }
        
        result = await n8n_trigger.gmail_reply(
            access_token=creds["gmail"]["access_token"],
            message_id=email_ref["id"],
            reply_text=reply_content
        )
        
        if result["status"] == "success":
            return {
                "type": "api_response",
                "data": result["data"],
                "voice_response": "Reply sent successfully."
            }
    
    # Maps actions
    elif intent == Intent.MAPS_DISTANCE:
        destination = entities.get("destination")
        
        if not destination:
            return {
                "type": "clarification",
                "question": "Where would you like to go?",
                "voice_response": "Where would you like to go?"
            }
        
        maps_service = GoogleMapsService()
        distance_data = await maps_service.calculate_distance(
            "Current Location",
            destination
        )
        
        summary = maps_service.format_distance_summary(distance_data, destination)
        
        # Store location reference
        memory.store_context_reference("location", destination, destination)
        
        return {
            "type": "api_response",
            "data": distance_data,
            "voice_response": summary
        }
    
    # Spotify actions
    elif intent == Intent.SPOTIFY_PLAY:
        if "spotify" not in creds:
            return {
                "type": "error",
                "voice_response": "Spotify is not connected."
            }
        
        query = entities.get("query", "chill music")
        
        result = await n8n_trigger.spotify_control(
            access_token=creds["spotify"]["access_token"],
            action="play",
            query=query
        )
        
        if result["status"] == "success" and result["data"]:
            data = result["data"]
            
            if "track" in data:
                memory.store_context_reference(
                    "track",
                    data["track"]["uri"],
                    data["track"]["name"],
                    {"artist": data["track"]["artist"]}
                )
                
                return {
                    "type": "api_response",
                    "data": data,
                    "voice_response": f"Now playing {data['track']['name']} by {data['track']['artist']}"
                }
    
    elif intent == Intent.SPOTIFY_PAUSE:
        if "spotify" not in creds:
            return {
                "type": "error",
                "voice_response": "Spotify is not connected."
            }
        
        result = await n8n_trigger.spotify_control(
            access_token=creds["spotify"]["access_token"],
            action="pause"
        )
        
        return {
            "type": "api_response",
            "data": result["data"],
            "voice_response": "Paused."
        }
    
    return {
        "type": "error",
        "voice_response": "I couldn't complete that action."
    }


def get_service_credentials(db: Session) -> Dict[str, Any]:
    """Get all service credentials from database"""
    creds = {}
    
    services = db.query(ServiceCredentials).all()
    
    for service in services:
        creds[service.service] = {
            "access_token": service.access_token,
            "refresh_token": service.refresh_token,
            "expires_at": service.expires_at
        }
    
    return creds


@app.get("/api/services/status")
async def get_services_status(db: Session = Depends(get_db)):
    """Check which services are connected"""
    creds = get_service_credentials(db)
    
    return {
        "gmail": "connected" if "gmail" in creds else "disconnected",
        "spotify": "connected" if "spotify" in creds else "disconnected",
        "maps": "connected" if settings.GOOGLE_MAPS_API_KEY else "disconnected"
    }


@app.get("/api/memory/summary")
async def get_memory_summary(db: Session = Depends(get_db)):
    """Get memory summary for debugging"""
    memory = MemoryManager(db)
    return memory.get_memory_summary()


@app.post("/api/memory/clear")
async def clear_memory(db: Session = Depends(get_db)):
    """Clear all memory (for demo reset)"""
    db.query(ConversationMemory).delete()
    db.commit()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
