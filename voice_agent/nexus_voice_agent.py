"""
NEXUS Voice Agent - LiveKit Integration with Gemini
Smart automation assistant with natural voice interaction
Uses: Deepgram (STT + TTS) + Google Gemini (LLM)
"""
import os
import asyncio
import json
import httpx
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# System prompt for NEXUS AI agent
NEXUS_AGENT_SYSTEM_PROMPT = """You are NEXUS AI, a smart automation assistant that helps users with:

**Available Services:**
1. **Gmail Management**
   - Summarize recent emails ("check my emails", "what are my latest emails")
   - Send emails ("send email to john@example.com about meeting")
   - Always ask for clarification if email details are incomplete

2. **Google Maps**
   - Get distance and duration between locations ("distance from Mumbai to Delhi")
   - Provide travel information and route details
   - Always confirm both origin and destination

3. **General Assistance**
   - Answer questions about services
   - Clarify user intent if unclear
   - Help users formulate proper commands

**Your Behavior:**
- Be conversational, friendly, and professional
- Always confirm before performing actions (sending emails, etc.)
- If user request is unclear or missing information, ask specific clarifying questions
- Explain what you're doing in simple terms
- After completing an action, provide clear confirmation
- If a service is unavailable, explain alternative options

**Important Rules:**
1. For email sending: Always confirm recipient, subject, and message content
2. For maps: Always confirm both origin and destination cities
3. Never assume information - always ask if something is unclear
4. Keep responses concise but informative
5. Use natural, conversational language

**Communication with Backend:**
When user makes a request, you will:
1. Understand the intent (gmail, maps, or general)
2. Extract necessary parameters
3. Call the NEXUS backend to execute the action
4. Present results in a natural, conversational way

Be helpful, accurate, and always prioritize user understanding!
"""


class NEXUSVoiceAgent:
    """LiveKit voice agent for NEXUS automation platform using Gemini + Deepgram"""
    
    def __init__(
        self,
        deepgram_api_key: str,
        gemini_api_key: str,
        nexus_backend_url: str = "http://localhost:8000"
    ):
        self.deepgram_api_key = deepgram_api_key
        self.gemini_api_key = gemini_api_key
        self.nexus_backend_url = nexus_backend_url
        
        logger.info("NEXUS Voice Agent initialized with Gemini + Deepgram")
    
    async def process_user_command(self, user_text: str) -> str:
        """
        Process user command through NEXUS backend
        
        Args:
            user_text: User's spoken command
            
        Returns:
            Response text to speak back
        """
        try:
            logger.info(f"Processing command: {user_text}")
            
            # Call NEXUS backend API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.nexus_backend_url}/api/text/process",
                    json={"text": user_text}
                )
                response.raise_for_status()
                result = response.json()
            
            # Extract message from response
            if result.get("success"):
                message = result.get("message", "Done!")
                logger.info(f"✓ Backend response: {message[:100]}...")
                return message
            else:
                error_msg = result.get("message", "Sorry, something went wrong.")
                logger.error(f"✗ Backend error: {error_msg}")
                return error_msg
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling backend: {e}")
            return "Sorry, I'm having trouble connecting to the automation system. Please try again."
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return "Sorry, I encountered an error. Could you try rephrasing that?"
    
    async def entrypoint(self, ctx):
        """
        Main entrypoint for LiveKit agent
        This is called when agent joins a room
        """
        from livekit.agents import JobContext
        from livekit.agents.llm import ChatContext, ChatMessage
        from livekit.plugins import deepgram, google, silero
        from livekit import agents
        
        # Connect to room
        await ctx.connect()
        logger.info(f"✓ Connected to room: {ctx.room.name}")
        
        # Initialize chat context with system prompt
        initial_ctx = ChatContext(
            messages=[
                ChatMessage(
                    role="system",
                    content=NEXUS_AGENT_SYSTEM_PROMPT
                )
            ]
        )
        
        # Initialize voice components
        logger.info("Initializing voice components with Deepgram + Gemini...")
        
        # Speech-to-Text: Deepgram
        stt = deepgram.STT(api_key=self.deepgram_api_key)
        
        # Language Model: Google Gemini via LiveKit plugin
        llm = google.LLM(
            model="gemini-1.5-flash",  # Fast and efficient
            api_key=self.gemini_api_key
        )
        
        # Text-to-Speech: Deepgram TTS
        tts = deepgram.TTS(
            voice="aura-asteria-en",  # Natural, professional voice
            api_key=self.deepgram_api_key
        )
        
        # Create voice assistant
        assistant = agents.VoiceAssistant(
            vad=silero.VAD.load(),  # Voice Activity Detection
            stt=stt,  # Speech-to-Text
            llm=llm,  # Language Model
            tts=tts,  # Text-to-Speech
            chat_ctx=initial_ctx,
        )
        
        # Hook into assistant's function calling to integrate with NEXUS backend
        @assistant.on("function_calls_finished")
        async def on_function_calls_finished(called_functions):
            """Handle when assistant wants to call a function (execute action)"""
            logger.info(f"Function calls finished: {called_functions}")
        
        # Start the assistant
        assistant.start(ctx.room)
        
        # Send initial greeting
        await assistant.say(
            "Hello! I'm NEXUS AI, your smart automation assistant. "
            "I can help you with emails, maps, and more. What would you like me to do?",
            allow_interruptions=True
        )
        
        logger.info("✓ Voice agent started and ready for conversation")


async def run_agent(room_url: str, room_token: str):
    """
    Run the NEXUS voice agent in a LiveKit room
    
    Args:
        room_url: LiveKit server URL
        room_token: Access token for the room
    """
    from livekit import agents
    
    # Get credentials
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    nexus_backend_url = os.getenv("NEXUS_BACKEND_URL", "http://localhost:8000")
    
    if not deepgram_api_key or not gemini_api_key:
        raise ValueError("Missing API keys in environment variables")
    
    # Create agent instance
    agent = NEXUSVoiceAgent(
        deepgram_api_key=deepgram_api_key,
        gemini_api_key=gemini_api_key,
        nexus_backend_url=nexus_backend_url
    )
    
    # Run agent worker
    worker = agents.Worker(
        entrypoint_fnc=agent.entrypoint
    )
    
    await worker.run()


if __name__ == "__main__":
    """Local testing"""
    print("NEXUS Voice Agent - LiveKit Integration")
    print("Run this with proper LiveKit credentials")
    
    # Example usage
    asyncio.run(run_agent(
        room_url=os.getenv("LIVEKIT_URL"),
        room_token="your_token_here"
    ))
