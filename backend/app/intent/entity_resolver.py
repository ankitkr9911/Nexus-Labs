"""
Entity resolver - extracts and resolves entities from user input
Works with memory manager for context resolution
"""
from typing import Dict, Any, Optional, List
from app.memory.manager import MemoryManager
from app.memory.context import ContextResolver
import re


class EntityResolver:
    """Resolves entities and references from user input"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize entity resolver
        
        Args:
            memory_manager: Long-term memory manager instance
        """
        self.memory = memory_manager
        self.context_resolver = ContextResolver(memory_manager)
    
    def resolve_entities(
        self,
        user_input: str,
        intent: str,
        extracted_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entity resolution method
        
        Args:
            user_input: Raw user command
            intent: Detected intent
            extracted_params: Parameters extracted by intent detector
        
        Returns:
            Dictionary of resolved entities
        """
        entities = extracted_params.copy()
        
        # Check if input contains references
        context_info = self.context_resolver.extract_context_from_input(user_input)
        
        if context_info["has_reference"]:
            # Resolve reference
            if context_info["ordinal"]:
                # Handle "first email", "second one", etc.
                resolved = self.context_resolver.resolve_ordinal_reference(
                    context_info["ordinal"],
                    context_info["reference_type"] or "email"
                )
                if resolved:
                    entities["resolved_reference"] = resolved
            else:
                # Handle "that", "this", "it", etc.
                resolved = self.memory.resolve_entity_reference(user_input)
                if resolved:
                    entities["resolved_reference"] = resolved
        
        # Add context flag
        entities["needs_clarification"] = (
            context_info["has_reference"] and
            "resolved_reference" not in entities
        )
        
        return entities
    
    def extract_email_references(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Extract email-specific references
        
        Args:
            user_input: User command
        
        Returns:
            Email reference details or None
        """
        text_lower = user_input.lower()
        
        # Check for ordinal references
        ordinals = ["first", "second", "third", "last"]
        for ordinal in ordinals:
            if ordinal in text_lower and "email" in text_lower:
                return self.context_resolver.resolve_ordinal_reference(ordinal, "email")
        
        # Check for demonstrative references
        if any(word in text_lower for word in ["that email", "this email", "the email"]):
            refs = self.memory.get_last_reference("email", limit=1)
            if refs:
                return {
                    "type": "email",
                    "id": refs[0].ref_id,
                    "name": refs[0].ref_name,
                    "metadata": refs[0].metadata
                }
        
        return None
    
    def extract_location_references(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Extract location-specific references
        
        Args:
            user_input: User command
        
        Returns:
            Location reference details or None
        """
        text_lower = user_input.lower()
        
        # Check for demonstrative references
        if any(word in text_lower for word in ["there", "that place", "same place"]):
            refs = self.memory.get_last_reference("location", limit=1)
            if refs:
                return {
                    "type": "location",
                    "id": refs[0].ref_id,
                    "name": refs[0].ref_name,
                    "metadata": refs[0].metadata
                }
        
        return None
    
    def extract_sender_name(self, user_input: str) -> Optional[str]:
        """
        Extract sender name from email-related queries
        
        Args:
            user_input: User command
        
        Returns:
            Sender name or None
        """
        # Pattern: "emails from [Name]"
        pattern = r"(?:from|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        match = re.search(pattern, user_input)
        
        if match:
            return match.group(1)
        
        return None
    
    def needs_clarification(self, entities: Dict[str, Any]) -> bool:
        """
        Check if entities need clarification
        
        Args:
            entities: Resolved entities
        
        Returns:
            True if clarification needed
        """
        return entities.get("needs_clarification", False)
    
    def generate_clarification_options(
        self,
        ref_type: str
    ) -> Dict[str, Any]:
        """
        Generate clarification options for user
        
        Args:
            ref_type: Type of reference that needs clarification
        
        Returns:
            Dictionary with clarification question and options
        """
        recent_items = self.context_resolver.get_recent_items_summary(ref_type, limit=3)
        
        question = self.context_resolver.build_clarification_question(ref_type)
        
        return {
            "question": question,
            "options": recent_items,
            "type": ref_type
        }
