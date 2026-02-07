"""
Intent detection from user voice commands
Maps natural language to specific actions
"""
import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class Intent(str, Enum):
    """Supported intents in the system"""
    # Gmail
    GMAIL_SUMMARIZE = "gmail_summarize"
    GMAIL_READ = "gmail_read"
    GMAIL_REPLY = "gmail_reply"
    GMAIL_SEND = "gmail_send"
    GMAIL_OPEN_UI = "gmail_open_ui"
    
    # Google Maps
    MAPS_DISTANCE = "maps_distance"
    MAPS_DIRECTIONS = "maps_directions"
    MAPS_OPEN_UI = "maps_open_ui"
    
    # Spotify
    SPOTIFY_PLAY = "spotify_play"
    SPOTIFY_PAUSE = "spotify_pause"
    SPOTIFY_SEARCH = "spotify_search"
    SPOTIFY_OPEN_UI = "spotify_open_ui"
    
    # System
    UNKNOWN = "unknown"
    CLARIFY = "clarify"


class ActionType(str, Enum):
    """Type of action to perform"""
    API = "api"  # Execute via n8n workflow
    UI_HANDOFF = "ui_handoff"  # Open external UI
    CLARIFY = "clarify"  # Need more information


class IntentDetector:
    """Detects user intent from voice input"""
    
    def __init__(self):
        """Initialize intent patterns"""
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[Intent, list]:
        """
        Define regex patterns for each intent
        
        Returns:
            Dictionary mapping intents to pattern lists
        """
        return {
            # Gmail Intents
            Intent.GMAIL_SUMMARIZE: [
                r"summarize.*email",
                r"email.*summary",
                r"what.*email",
                r"check.*email",
                r"any.*email",
                r"show.*email",
            ],
            Intent.GMAIL_REPLY: [
                r"reply.*email",
                r"respond.*email",
                r"answer.*email",
                r"write back",
            ],
            Intent.GMAIL_OPEN_UI: [
                r"open.*gmail",
                r"show.*gmail",
                r"take me to gmail",
            ],
            
            # Google Maps Intents
            Intent.MAPS_DISTANCE: [
                r"how far.*",
                r"distance.*",
                r"how long.*take",
                r"travel time.*",
            ],
            Intent.MAPS_DIRECTIONS: [
                r"directions.*",
                r"navigate.*",
                r"take me.*",
                r"how do i get.*",
                r"route.*",
            ],
            Intent.MAPS_OPEN_UI: [
                r"open.*maps",
                r"show.*maps",
            ],
            
            # Spotify Intents
            Intent.SPOTIFY_PLAY: [
                r"play.*",
                r"start.*music",
                r"put on.*",
                r"listen.*",
            ],
            Intent.SPOTIFY_PAUSE: [
                r"pause.*",
                r"stop.*music",
                r"stop playing",
            ],
            Intent.SPOTIFY_OPEN_UI: [
                r"open.*spotify",
                r"show.*spotify",
            ],
        }
    
    def detect(self, user_input: str) -> Tuple[Intent, ActionType]:
        """
        Detect intent from user input
        
        Args:
            user_input: Raw voice command text
        
        Returns:
            Tuple of (Intent, ActionType)
        """
        user_input_lower = user_input.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    action_type = self._determine_action_type(intent, user_input_lower)
                    return intent, action_type
        
        # No match found
        return Intent.UNKNOWN, ActionType.CLARIFY
    
    def _determine_action_type(self, intent: Intent, user_input: str) -> ActionType:
        """
        Determine if intent requires API call or UI handoff
        
        Args:
            intent: Detected intent
            user_input: User's command
        
        Returns:
            ActionType
        """
        # UI handoff intents
        ui_handoff_intents = [
            Intent.GMAIL_OPEN_UI,
            Intent.MAPS_OPEN_UI,
            Intent.MAPS_DIRECTIONS,
            Intent.SPOTIFY_OPEN_UI,
        ]
        
        if intent in ui_handoff_intents:
            return ActionType.UI_HANDOFF
        
        # Check if user explicitly asks to "open" or "show"
        if any(word in user_input for word in ["open", "show me", "display"]):
            return ActionType.UI_HANDOFF
        
        # Default to API action
        return ActionType.API
    
    def extract_parameters(
        self,
        intent: Intent,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Extract parameters from user input based on intent
        
        Args:
            intent: Detected intent
            user_input: User's command
        
        Returns:
            Dictionary of extracted parameters
        """
        params = {}
        user_input_lower = user_input.lower()
        
        # Gmail parameters
        if intent == Intent.GMAIL_REPLY:
            # Extract reply content
            reply_patterns = [
                r"saying\s+(.+)",
                r"tell them\s+(.+)",
                r"message\s+(.+)",
            ]
            for pattern in reply_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    params["reply_content"] = match.group(1).strip()
                    break
        
        # Maps parameters
        if intent in [Intent.MAPS_DISTANCE, Intent.MAPS_DIRECTIONS]:
            # Extract location
            location_patterns = [
                r"to\s+(.+?)(?:\?|$)",
                r"from here to\s+(.+?)(?:\?|$)",
            ]
            for pattern in location_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    params["destination"] = match.group(1).strip()
                    break
        
        # Spotify parameters
        if intent == Intent.SPOTIFY_PLAY:
            # Extract song/artist/genre
            play_patterns = [
                r"play\s+(.+?)(?:\s+by\s+|\s+music|\s+song|$)",
                r"put on\s+(.+)",
            ]
            for pattern in play_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    params["query"] = match.group(1).strip()
                    break
        
        return params
    
    def get_intent_description(self, intent: Intent) -> str:
        """
        Get human-readable description of intent
        
        Args:
            intent: Intent enum
        
        Returns:
            Description string
        """
        descriptions = {
            Intent.GMAIL_SUMMARIZE: "Summarize emails",
            Intent.GMAIL_REPLY: "Reply to email",
            Intent.GMAIL_OPEN_UI: "Open Gmail interface",
            Intent.MAPS_DISTANCE: "Calculate distance",
            Intent.MAPS_DIRECTIONS: "Get directions",
            Intent.SPOTIFY_PLAY: "Play music",
            Intent.SPOTIFY_PAUSE: "Pause music",
            Intent.UNKNOWN: "Unknown intent",
        }
        return descriptions.get(intent, "Unknown")
