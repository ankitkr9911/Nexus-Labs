"""
Long-term memory manager for NEXUS AI
Handles persistent context and entity resolution across sessions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import ConversationMemory, ContextReferences
import json


class MemoryManager:
    """Manages long-term memory and context resolution"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_interaction(
        self,
        user_input: str,
        intent: str,
        entities: Dict[str, Any],
        action_taken: str,
        result_summary: str
    ) -> ConversationMemory:
        """
        Store a complete interaction in long-term memory
        
        Args:
            user_input: Raw user voice command
            intent: Detected intent (e.g., 'gmail_summarize')
            entities: Extracted entities as dictionary
            action_taken: What action was performed
            result_summary: Summary of the result
        
        Returns:
            ConversationMemory object
        """
        memory = ConversationMemory(
            user_input=user_input,
            intent=intent,
            entities=entities,
            action_taken=action_taken,
            result_summary=result_summary
        )
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory
    
    def store_context_reference(
        self,
        ref_type: str,
        ref_id: str,
        ref_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextReferences:
        """
        Store a reference for later resolution (e.g., "that email")
        
        Args:
            ref_type: Type of reference ('email', 'location', 'track', etc.)
            ref_id: Actual ID from the service
            ref_name: Human-readable description
            metadata: Additional context data
        
        Returns:
            ContextReferences object
        """
        # Check if reference already exists
        existing = self.db.query(ContextReferences).filter(
            ContextReferences.ref_type == ref_type,
            ContextReferences.ref_id == ref_id
        ).first()
        
        if existing:
            # Update existing reference
            existing.last_accessed = datetime.utcnow()
            existing.access_count += 1
            existing.ref_name = ref_name
            if metadata:
                existing.metadata = metadata
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new reference
            reference = ContextReferences(
                ref_type=ref_type,
                ref_id=ref_id,
                ref_name=ref_name,
                metadata=metadata or {}
            )
            self.db.add(reference)
            self.db.commit()
            self.db.refresh(reference)
            return reference
    
    def get_last_reference(
        self,
        ref_type: str,
        limit: int = 1
    ) -> Optional[List[ContextReferences]]:
        """
        Get the most recent reference of a specific type
        Used for resolving "that email", "there", etc.
        
        Args:
            ref_type: Type of reference to retrieve
            limit: Number of references to retrieve
        
        Returns:
            List of ContextReferences or None
        """
        references = self.db.query(ContextReferences).filter(
            ContextReferences.ref_type == ref_type
        ).order_by(
            ContextReferences.last_accessed.desc()
        ).limit(limit).all()
        
        return references if references else None
    
    def get_recent_context(
        self,
        intent_filter: Optional[str] = None,
        limit: int = 5
    ) -> List[ConversationMemory]:
        """
        Get recent conversation history
        
        Args:
            intent_filter: Filter by specific intent (optional)
            limit: Number of records to retrieve
        
        Returns:
            List of ConversationMemory objects
        """
        query = self.db.query(ConversationMemory)
        
        if intent_filter:
            query = query.filter(ConversationMemory.intent == intent_filter)
        
        return query.order_by(
            ConversationMemory.timestamp.desc()
        ).limit(limit).all()
    
    def resolve_entity_reference(
        self,
        reference_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve vague references like "that", "there", "it"
        
        Args:
            reference_text: Text containing reference (e.g., "that email")
        
        Returns:
            Dictionary with resolved entity or None
        """
        text_lower = reference_text.lower()
        
        # Email references
        if "email" in text_lower or "message" in text_lower:
            ref = self.get_last_reference("email")
            if ref:
                return {
                    "type": "email",
                    "id": ref[0].ref_id,
                    "name": ref[0].ref_name,
                    "metadata": ref[0].metadata
                }
        
        # Location references
        if any(word in text_lower for word in ["there", "that place", "location"]):
            ref = self.get_last_reference("location")
            if ref:
                return {
                    "type": "location",
                    "id": ref[0].ref_id,
                    "name": ref[0].ref_name,
                    "metadata": ref[0].metadata
                }
        
        # Music references
        if any(word in text_lower for word in ["song", "track", "music", "it"]):
            ref = self.get_last_reference("track")
            if ref:
                return {
                    "type": "track",
                    "id": ref[0].ref_id,
                    "name": ref[0].ref_name,
                    "metadata": ref[0].metadata
                }
        
        return None
    
    def clear_old_references(self, days: int = 7):
        """
        Clean up old references to prevent memory bloat
        
        Args:
            days: Delete references older than this many days
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        self.db.query(ContextReferences).filter(
            ContextReferences.last_accessed < cutoff_date
        ).delete()
        
        self.db.commit()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get summary of stored memory for debugging/display
        
        Returns:
            Dictionary with memory statistics
        """
        total_interactions = self.db.query(ConversationMemory).count()
        total_references = self.db.query(ContextReferences).count()
        
        recent_intents = self.db.query(
            ConversationMemory.intent
        ).order_by(
            ConversationMemory.timestamp.desc()
        ).limit(10).all()
        
        return {
            "total_interactions": total_interactions,
            "total_references": total_references,
            "recent_intents": [i[0] for i in recent_intents]
        }
