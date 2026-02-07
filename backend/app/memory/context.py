"""
Context resolution utilities
Helps resolve ambiguous references in user commands
"""
from typing import Dict, Any, Optional, List
from app.memory.manager import MemoryManager


class ContextResolver:
    """Resolves context from user input using memory"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
    
    def resolve_ordinal_reference(
        self,
        ordinal: str,
        ref_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve ordinal references like "first", "second", "last"
        
        Args:
            ordinal: The ordinal word (first, second, last, etc.)
            ref_type: Type of reference to look up
        
        Returns:
            Resolved entity or None
        """
        ordinal_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": -1
        }
        
        if ordinal.lower() not in ordinal_map:
            return None
        
        index = ordinal_map[ordinal.lower()]
        refs = self.memory.get_last_reference(ref_type, limit=5)
        
        if not refs:
            return None
        
        try:
            selected_ref = refs[index]
            return {
                "type": ref_type,
                "id": selected_ref.ref_id,
                "name": selected_ref.ref_name,
                "metadata": selected_ref.metadata
            }
        except IndexError:
            return None
    
    def extract_context_from_input(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Extract contextual clues from user input
        
        Args:
            user_input: Raw user command
        
        Returns:
            Dictionary of extracted context
        """
        context = {
            "has_reference": False,
            "reference_type": None,
            "ordinal": None,
            "needs_clarification": False
        }
        
        text_lower = user_input.lower()
        
        # Check for ordinal references
        ordinals = ["first", "second", "third", "fourth", "fifth", "last"]
        for ordinal in ordinals:
            if ordinal in text_lower:
                context["has_reference"] = True
                context["ordinal"] = ordinal
                break
        
        # Check for demonstrative references
        demonstratives = ["that", "this", "it", "there"]
        for demo in demonstratives:
            if demo in text_lower:
                context["has_reference"] = True
                break
        
        # Determine reference type
        if "email" in text_lower or "message" in text_lower:
            context["reference_type"] = "email"
        elif any(word in text_lower for word in ["place", "location", "there"]):
            context["reference_type"] = "location"
        elif any(word in text_lower for word in ["song", "track", "music"]):
            context["reference_type"] = "track"
        
        return context
    
    def build_clarification_question(
        self,
        missing_context: str
    ) -> str:
        """
        Generate clarification question when context is ambiguous
        
        Args:
            missing_context: What information is missing
        
        Returns:
            Question to ask user
        """
        questions = {
            "email": "Which email? Could you be more specific?",
            "location": "Which location do you mean?",
            "track": "Which song are you referring to?",
            "general": "Could you please clarify what you mean?"
        }
        
        return questions.get(missing_context, questions["general"])
    
    def get_recent_items_summary(
        self,
        ref_type: str,
        limit: int = 3
    ) -> List[str]:
        """
        Get human-readable summary of recent items for clarification
        
        Args:
            ref_type: Type of items to summarize
            limit: Number of items to include
        
        Returns:
            List of item descriptions
        """
        refs = self.memory.get_last_reference(ref_type, limit=limit)
        
        if not refs:
            return []
        
        return [ref.ref_name for ref in refs]
