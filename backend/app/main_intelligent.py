"""
Simplified FastAPI backend for NEXUS AI
Routes ALL intelligence to n8n workflow with Gemini decision-making
+ LiveKit Voice Agent Integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import httpx
import base64
import os
import sys

from app.config import settings
from app.database import get_db, init_db, SessionLocal
from app.memory.manager import MemoryManager

# Add voice_agent directory to path for LiveKit imports
voice_agent_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "voice_agent")
if voice_agent_path not in sys.path:
    sys.path.insert(0, voice_agent_path)

# Import LiveKit room manager (optional - only if dependencies installed)
try:
    from livekit_room_manager import LiveKitRoomManager, get_room_manager
    LIVEKIT_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✓ LiveKit integration available")
except ImportError:
    LIVEKIT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠ LiveKit not available - install dependencies: pip install -r voice_agent/livekit_requirements.txt")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NEXUS AI Backend",
    description="Voice-First AI Platform - Routes to intelligent n8n workflow",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory manager (for context storage only)
db = SessionLocal()
memory_manager = MemoryManager(db)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("🚀 NEXUS AI Backend Started")
    logger.info("📡 All intelligence delegated to n8n + Gemini workflow")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NEXUS AI - Intelligent Voice Automation",
        "status": "online",
        "architecture": "n8n + Gemini LLM decision-making",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NEXUS AI"}


@app.post("/api/text/process")
async def process_command(request: dict):
    """
    Process ANY user command - sends to intelligent n8n workflow
    
    The n8n workflow contains Gemini LLM that:
    1. Understands user intent
    2. Decides which service to use
    3. Extracts parameters
    4. Routes to appropriate action
    
    This endpoint just passes through to n8n and stores memory
    """
    try:
        # Accept both 'message' (from voice) and 'text' (from other sources)
        user_text = request.get("message") or request.get("text", "")
        if not user_text:
            return {
                "success": False,
                "response": "No command provided"
            }
        
        logger.info(f"📝 User command: {user_text}")
        
        # Get recent memory for context
        recent_interactions = memory_manager.get_recent_context(limit=5)
        context_text = "\n".join([
            f"- User said: '{interaction.user_input}' → Result: {interaction.result_summary}"
            for interaction in recent_interactions
        ])
        
        logger.info(f"🧠 Context: {len(recent_interactions)} recent interactions")
        
        # Call intelligent n8n workflow
        webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/nexus-agent"
        
        payload = {
            "user_request": user_text,
            "context": context_text or "No previous context",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"🚀 Calling n8n workflow at {webhook_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            
            # Debug: Log raw response
            logger.info(f"📡 n8n raw response status: {response.status_code}")
            logger.info(f"📡 n8n raw response headers: {response.headers.get('content-type')}")
            logger.info(f"📡 n8n raw response text: {response.text[:500]}")  # First 500 chars
            
            # Try to parse JSON
            try:
                raw_result = response.json()
            except Exception as json_error:
                logger.error(f"❌ Failed to parse n8n response as JSON: {json_error}")
                logger.error(f"📄 Full response text: {response.text}")
                raise ValueError(f"n8n returned invalid JSON: {response.text[:200]}")
        
        # n8n returns array [{"text": "..."}] when using responseNode mode
        # Extract first item if it's an array
        if isinstance(raw_result, list) and len(raw_result) > 0:
            result = raw_result[0]
        else:
            result = raw_result
        
        logger.info(f"✅ n8n response received: {type(result)}")
        logger.info(f"📦 Response data: {result}")
        
        # Store interaction in memory
        memory_manager.store_interaction(
            user_input=user_text,
            intent=result.get("service", "unknown"),
            entities=result.get("parameters", {}),
            action_taken=result.get("action", "unknown"),
            result_summary=result.get("summary") or result.get("text") or str(result)
        )
        
        # Handle clarification requests from Gemini
        if result.get("needs_clarification"):
            return {
                "success": False,
                "response": result.get("clarification_question", "Could you provide more details?"),
                "needs_clarification": True
            }
        
        # Return successful result
        # n8n returns 'text' field from LLM chains or structured data
        message = result.get("text") or result.get("message") or result.get("summary") or str(result)
        
        # Special handling for maps queries - handle multiple travel modes
        if result.get("service") == "maps":
            # Extract origin and destination from multiple possible locations
            origin = (result.get("origin") or 
                     result.get("parameters", {}).get("origin") or 
                     result.get("data", {}).get("origin"))
            destination = (result.get("destination") or 
                          result.get("parameters", {}).get("destination") or 
                          result.get("data", {}).get("destination"))
            
            # Check if we have structured mode data
            driving = result.get("driving", {})
            walking = result.get("walking", {})
            transit = result.get("transit", {})
            
            # Build voice-friendly response with all modes
            if driving.get("distance") or walking.get("distance") or transit.get("distance"):
                response_parts = [f"Here are the routes from {origin} to {destination}:"]
                
                if driving.get("distance"):
                    response_parts.append(f"By car: {driving['distance']}, takes {driving['duration']}")
                if walking.get("distance"):
                    response_parts.append(f"Walking: {walking['distance']}, takes {walking['duration']}")
                if transit.get("distance"):
                    response_parts.append(f"By transit: {transit['distance']}, takes {transit['duration']}")
                
                response_parts.append("Say give me directions to open Google Maps.")
                cleaned_message = ". ".join(response_parts)
            else:
                # Fallback: use the text response from n8n
                cleaned_message = message
                # Ensure it ends with the directions prompt
                if "give me directions" not in cleaned_message.lower():
                    cleaned_message += " Say give me directions to open Google Maps."
        else:
            # Clean up ALL markdown and special characters for better voice experience
            cleaned_message = (message
                .replace("**", "")      # Bold
                .replace("*", "")       # Italic
                .replace("###", "")     # Headers
                .replace("##", "")
                .replace("#", "")
                .replace("---", "")     # Horizontal rules
                .replace("...", "")     # Ellipsis
                .replace("```", "")     # Code blocks
                .replace("`", "")       # Inline code
                .replace("~~", "")      # Strikethrough
            )
        
        # Extract origin and destination for maps queries from result
        origin = (result.get("origin") or 
                 result.get("parameters", {}).get("origin") or 
                 result.get("data", {}).get("origin"))
        destination = (result.get("destination") or 
                      result.get("parameters", {}).get("destination") or 
                      result.get("data", {}).get("destination"))
        
        return {
            "success": True,
            "response": cleaned_message,  # Voice client expects 'response' field
            "message": cleaned_message,   # Keep for backward compatibility
            "data": result,
            "service": result.get("service"),
            "action": result.get("action"),
            "reasoning": result.get("reasoning"),
            "origin": origin,
            "destination": destination
        }
        
    except httpx.HTTPError as e:
        logger.error(f"❌ n8n workflow error: {e}")
        return {
            "success": False,
            "response": "The automation workflow is not available. Please make sure n8n is running at http://localhost:5678",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"❌ Error processing command: {e}")
        return {
            "success": False,
            "response": "An error occurred processing your request",
            "error": str(e)
        }


@app.post("/api/voice/transcribe")
async def transcribe_audio(request: dict):
    """
    Transcribe audio using Deepgram, then send to intelligent workflow
    
    Expected payload:
    {
        "audio": "base64_encoded_audio",
        "format": "audio/wav"
    }
    """
    try:
        # Decode audio
        audio_bytes = base64.b64decode(request["audio"])
        audio_format = request.get("format", "audio/wav")
        
        # Transcribe with Deepgram
        if settings.DEEPGRAM_API_KEY:
            from app.voice.deepgram import DeepgramTranscriber
            transcriber = DeepgramTranscriber()
            transcript = await transcriber.transcribe_audio(audio_bytes, mimetype=audio_format)
            
            if not transcript:
                return {
                    "success": False,
                    "message": "Could not transcribe audio"
                }
            
            logger.info(f"🎤 Transcribed: {transcript}")
            
            # Process the transcript through intelligent workflow
            result = await process_command({"text": transcript})
            result["transcript"] = transcript
            
            return result
        else:
            return {
                "success": False,
                "message": "Deepgram API key not configured. Use text input instead."
            }
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {
            "success": False,
            "message": "Error processing audio",
            "error": str(e)
        }


@app.get("/api/services/status")
async def service_status():
    """
    Check if n8n workflow is available
    """
    try:
        webhook_url = f"{settings.N8N_WEBHOOK_BASE_URL}/nexus-agent"
        
        # Test connection with simple health check payload
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                webhook_url,
                json={"user_request": "health check", "context": ""}
            )
            
        if response.status_code == 200:
            return {
                "n8n_workflow": "connected",
                "workflow_url": webhook_url
            }
        else:
            return {
                "n8n_workflow": "disconnected",
                "workflow_url": webhook_url
            }
            
    except Exception as e:
        logger.error(f"Service status check failed: {e}")
        return {
            "n8n_workflow": "disconnected",
            "error": str(e)
        }


@app.get("/api/memory/summary")
async def memory_summary():
    """Get summary of stored interactions"""
    try:
        interactions = memory_manager.get_recent_context(limit=10)
        
        return {
            "total_interactions": len(interactions),
            "recent_interactions": [
                {
                    "command": i.user_input,
                    "intent": i.intent,
                    "result": i.result_summary,
                    "timestamp": i.timestamp.isoformat()
                }
                for i in interactions
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching memory: {e}")
        return {"error": str(e)}


@app.post("/api/vapi/webhook")
async def vapi_webhook(request: dict):
    """
    Vapi.ai webhook endpoint - receives voice interactions from Vapi
    
    Vapi sends:
    - message.type: "function-call" when user speaks
    - message.functionCall.name: function name
    - message.functionCall.parameters: extracted parameters
    
    We process through n8n and return response
    """
    try:
        logger.info(f"🎙️ Vapi webhook received: {request}")
        
        message = request.get("message", {})
        message_type = message.get("type")
        
        # Handle function calls from Vapi
        if message_type == "function-call":
            function_call = message.get("functionCall", {})
            function_name = function_call.get("name")
            parameters = function_call.get("parameters", {})
            
            logger.info(f"📞 Vapi function call: {function_name} with params: {parameters}")
            
            # Convert to natural language for n8n
            if function_name == "check_emails":
                user_text = f"Check my emails and summarize them"
            elif function_name == "send_email":
                to = parameters.get("to", "")
                subject = parameters.get("subject", "")
                user_text = f"Send an email to {to} about {subject}"
            elif function_name == "get_distance":
                origin = parameters.get("origin", "")
                destination = parameters.get("destination", "")
                user_text = f"What's the distance from {origin} to {destination}"
                
                # Process through n8n
                result = await process_command({"text": user_text})
                
                # Generate Google Maps directions URL
                import urllib.parse
                maps_url = f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}&destination={urllib.parse.quote(destination)}&travelmode=driving"
                
                # Enhance response with directions link
                response_text = result.get("message", "")
                response_text += f"\n\nYou can view detailed directions here: {maps_url}"
                
                return {
                    "results": [{
                        "result": response_text,
                        "toolCallId": message.get("toolCallId")
                    }]
                }
            elif function_name == "general_assistance":
                query = parameters.get("query", "")
                user_text = query
            else:
                user_text = parameters.get("query", "I need help")
            
            # Process through existing n8n workflow
            result = await process_command({"text": user_text})
            
            # Return response in Vapi format
            return {
                "results": [{
                    "result": result.get("message", "I've processed your request"),
                    "toolCallId": message.get("toolCallId")
                }]
            }
        
        # Handle end-of-call summary requests
        elif message_type == "end-of-call-report":
            logger.info("📊 Vapi call ended")
            return {"status": "ok"}
        
        # Default response
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Vapi webhook error: {e}")
        return {
            "results": [{
                "result": "I encountered an error processing your request. Please try again.",
                "error": str(e)
            }]
        }


# ==========================================
# LiveKit Voice Agent Endpoints
# ==========================================

@app.post("/api/livekit/create-room")
async def create_livekit_room(request: dict):
    """
    Create a LiveKit room for voice agent conversation
    
    Payload:
    {
        "user_name": "John Doe",
        "room_name": "nexus_conversation_123" (optional - auto-generated if not provided)
    }
    
    Returns connection token and room details
    """
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LiveKit integration not available. Install dependencies: pip install -r voice_agent/livekit_requirements.txt"
        )
    
    try:
        user_name = request.get("user_name", "Guest")
        room_name = request.get("room_name")
        
        # Generate room name if not provided
        if not room_name:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            room_name = f"nexus_{timestamp}"
        
        # Get room manager
        room_mgr = get_room_manager()
        
        # Create room (optional - LiveKit creates automatically on join)
        try:
            room_details = await room_mgr.create_room(
                room_name=room_name,
                empty_timeout=600,  # 10 minutes
                max_participants=10
            )
            logger.info(f"✓ Created LiveKit room: {room_name}")
        except Exception as e:
            logger.warning(f"Room may already exist: {e}")
            room_details = {"name": room_name}
        
        # Generate token for user
        token_data = room_mgr.create_room_token(
            room_name=room_name,
            participant_name=user_name,
            max_duration_seconds=3600  # 1 hour
        )
        
        logger.info(f"✓ Generated token for {user_name} in room {room_name}")
        
        return {
            "success": True,
            "message": "LiveKit room ready",
            "token": token_data["token"],
            "url": token_data["url"],
            "room_name": room_name,
            "participant_name": user_name,
            "expires_in": token_data["expires_in"],
            "agent_info": {
                "name": "NEXUS",
                "capabilities": [
                    "Email management (Gmail)",
                    "Navigation & directions (Google Maps)",
                    "Music control (Spotify)",
                    "General assistance"
                ]
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating LiveKit room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/livekit/rooms")
async def list_livekit_rooms():
    """List all active LiveKit rooms"""
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LiveKit integration not available"
        )
    
    try:
        room_mgr = get_room_manager()
        rooms = await room_mgr.list_rooms()
        
        return {
            "success": True,
            "rooms": rooms,
            "count": len(rooms)
        }
    
    except Exception as e:
        logger.error(f"Error listing rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/livekit/room/{room_name}")
async def delete_livekit_room(room_name: str):
    """Delete a LiveKit room"""
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LiveKit integration not available"
        )
    
    try:
        room_mgr = get_room_manager()
        success = await room_mgr.delete_room(room_name)
        
        if success:
            return {
                "success": True,
                "message": f"Room {room_name} deleted"
            }
        else:
            raise HTTPException(status_code=404, detail="Room not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/livekit/status")
async def livekit_status():
    """Check LiveKit integration status"""
    return {
        "available": LIVEKIT_AVAILABLE,
        "livekit_url": os.environ.get("LIVEKIT_URL") if LIVEKIT_AVAILABLE else None,
        "configured": bool(
            os.environ.get("LIVEKIT_URL") and 
            os.environ.get("LIVEKIT_API_KEY") and 
            os.environ.get("LIVEKIT_API_SECRET")
        )
    }


# ==================== VAPI INTEGRATION ====================

@app.post("/vapi/check-emails")
async def vapi_check_emails(request: dict):
    """
    VAPI function: Check emails
    Called by VAPI assistant when user asks to check emails
    """
    try:
        # Extract parameters from VAPI request
        message = request.get("message", {})
        function_call = message.get("functionCall", {})
        parameters = function_call.get("parameters", {})
        
        count = parameters.get("count", 1)
        
        logger.info(f"📧 VAPI: Check {count} emails")
        
        # Call n8n workflow
        user_request = f"Check my latest {count} email(s)"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json={"user_request": user_request},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "result": result.get("output", "Emails checked successfully")
                }
            else:
                return {
                    "result": "Sorry, I couldn't check your emails right now."
                }
                
    except Exception as e:
        logger.error(f"VAPI check-emails error: {e}")
        return {
            "result": f"Error checking emails: {str(e)}"
        }


@app.post("/vapi/send-email")
async def vapi_send_email(request: dict):
    """
    VAPI function: Send email
    Called by VAPI assistant when user asks to send an email
    """
    try:
        # Extract parameters from VAPI request
        message = request.get("message", {})
        function_call = message.get("functionCall", {})
        parameters = function_call.get("parameters", {})
        
        to = parameters.get("to")
        subject = parameters.get("subject")
        message_body = parameters.get("message")
        
        logger.info(f"📤 VAPI: Send email to {to}")
        
        # Call n8n workflow
        user_request = f"Send email to {to} with subject '{subject}' and message: {message_body}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json={"user_request": user_request},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "result": result.get("output", f"Email sent to {to} successfully")
                }
            else:
                return {
                    "result": "Sorry, I couldn't send the email right now."
                }
                
    except Exception as e:
        logger.error(f"VAPI send-email error: {e}")
        return {
            "result": f"Error sending email: {str(e)}"
        }


@app.post("/vapi/get-distance")
async def vapi_get_distance(request: dict):
    """
    VAPI function: Get distance
    Called by VAPI assistant when user asks for directions
    """
    try:
        # Extract parameters from VAPI request
        message = request.get("message", {})
        function_call = message.get("functionCall", {})
        parameters = function_call.get("parameters", {})
        
        origin = parameters.get("origin")
        destination = parameters.get("destination")
        
        logger.info(f"🗺️ VAPI: Get distance from {origin} to {destination}")
        
        # Call n8n workflow
        user_request = f"Get distance from {origin} to {destination}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.n8n_webhook_url,
                json={"user_request": user_request},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "result": result.get("output", f"Route calculated successfully")
                }
            else:
                return {
                    "result": "Sorry, I couldn't calculate the route right now."
                }
                
    except Exception as e:
        logger.error(f"VAPI get-distance error: {e}")
        return {
            "result": f"Error getting distance: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
