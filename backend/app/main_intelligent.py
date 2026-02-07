"""
Simplified FastAPI backend for NEXUS AI
Routes ALL intelligence to n8n workflow with Gemini decision-making
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import httpx
import base64

from app.config import settings
from app.database import get_db, init_db, SessionLocal
from app.memory.manager import MemoryManager

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
        user_text = request.get("text", "")
        if not user_text:
            return {
                "success": False,
                "message": "No command provided"
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
            raw_result = response.json()
        
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
                "message": result.get("clarification_question", "Could you provide more details?"),
                "needs_clarification": True
            }
        
        # Return successful result
        # n8n returns 'text' field from LLM chains or structured data
        message = result.get("text") or result.get("message") or result.get("summary") or str(result)
        
        return {
            "success": True,
            "message": message,
            "data": result,
            "service": result.get("service"),
            "action": result.get("action"),
            "reasoning": result.get("reasoning")
        }
        
    except httpx.HTTPError as e:
        logger.error(f"❌ n8n workflow error: {e}")
        return {
            "success": False,
            "message": "The automation workflow is not available. Please make sure n8n is running at http://localhost:5678",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"❌ Error processing command: {e}")
        return {
            "success": False,
            "message": "An error occurred processing your request",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
