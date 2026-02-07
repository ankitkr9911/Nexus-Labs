"""
Database models for NEXUS AI
Defines long-term memory, credentials, and context storage
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class ConversationMemory(Base):
    """
    Stores all user interactions for long-term memory
    Enables context resolution like "that email" or "there"
    """
    __tablename__ = "conversation_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_input = Column(Text, nullable=False)
    intent = Column(String(100))
    entities = Column(JSON)  # Stores extracted entities as JSON
    action_taken = Column(String(200))
    result_summary = Column(Text)


class ServiceCredentials(Base):
    """
    Stores OAuth tokens for integrated services
    Single-user demo: one row per service
    """
    __tablename__ = "service_credentials"
    
    service = Column(String(50), primary_key=True)  # 'gmail', 'spotify', 'maps'
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    extra_data = Column(JSON)  # Additional service-specific data


class ContextReferences(Base):
    """
    Tracks recent entities for quick reference resolution
    Example: "Reply to that email" → retrieves last email_id
    """
    __tablename__ = "context_references"
    
    id = Column(Integer, primary_key=True, index=True)
    ref_type = Column(String(50), index=True)  # 'email', 'location', 'track', 'playlist'
    ref_id = Column(String(200))  # Actual ID from service
    ref_name = Column(String(500))  # Human-readable description
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    access_count = Column(Integer, default=1)
    extra_data = Column(JSON)  # Additional context data
