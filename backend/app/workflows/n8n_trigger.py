"""
n8n webhook trigger module
Sends requests to self-hosted n8n workflows
"""
import httpx
from typing import Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class N8nWorkflowTrigger:
    """Triggers n8n workflows via webhooks"""
    
    def __init__(self):
        """Initialize n8n trigger"""
        self.base_url = settings.N8N_WEBHOOK_BASE_URL
        self.api_key = settings.N8N_API_KEY
    
    async def trigger_workflow(
        self,
        workflow_name: str,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Trigger an n8n workflow via webhook
        
        Args:
            workflow_name: Name of the workflow (used in webhook path)
            payload: Data to send to workflow
            timeout: Request timeout in seconds
        
        Returns:
            Workflow response data
        """
        webhook_url = f"{self.base_url}/{workflow_name}"
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
                
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "data": response.json() if response.text else None
                }
                
        except httpx.TimeoutException:
            logger.error(f"Workflow {workflow_name} timed out")
            return {"status": "error", "message": "Workflow execution timed out"}
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Workflow {workflow_name} failed with status {e.response.status_code}")
            return {"status": "error", "message": f"HTTP {e.response.status_code}"}
        
        except Exception as e:
            logger.error(f"Workflow {workflow_name} error: {e}")
            return {"status": "error", "message": str(e)}
    
    # Specific workflow triggers
    
    async def gmail_summarize(
        self,
        access_token: str,
        max_results: int = 10,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger Gmail summarization workflow
        
        Args:
            access_token: Gmail OAuth token
            max_results: Number of emails to fetch
            query: Gmail search query
        
        Returns:
            Workflow response with email summary
        """
        payload = {
            "access_token": access_token,
            "max_results": max_results,
            "query": query or "is:unread"
        }
        
        return await self.trigger_workflow("gmail-summarize", payload)
    
    async def gmail_reply(
        self,
        access_token: str,
        message_id: str,
        reply_text: str
    ) -> Dict[str, Any]:
        """
        Trigger Gmail reply workflow
        
        Args:
            access_token: Gmail OAuth token
            message_id: ID of email to reply to
            reply_text: Reply content
        
        Returns:
            Workflow response with sent message info
        """
        payload = {
            "access_token": access_token,
            "message_id": message_id,
            "reply_text": reply_text
        }
        
        return await self.trigger_workflow("gmail-reply", payload)
    
    async def maps_distance(
        self,
        origin: str,
        destination: str,
        modes: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Trigger Google Maps distance calculation workflow
        
        Args:
            origin: Starting location
            destination: Ending location
            modes: Travel modes to check
        
        Returns:
            Workflow response with distance/time data
        """
        payload = {
            "api_key": settings.GOOGLE_MAPS_API_KEY,
            "origin": origin,
            "destination": destination,
            "modes": modes or ["driving", "walking", "transit"]
        }
        
        return await self.trigger_workflow("maps-distance", payload)
    
    async def spotify_control(
        self,
        access_token: str,
        action: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger Spotify control workflow
        
        Args:
            access_token: Spotify OAuth token
            action: Action to perform (play, pause, search)
            query: Search query (for play action)
        
        Returns:
            Workflow response with playback status
        """
        payload = {
            "access_token": access_token,
            "action": action,
            "query": query
        }
        
        return await self.trigger_workflow("spotify-control", payload)
