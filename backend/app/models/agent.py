"""
Agent model
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Agent(Base):
    """Agent entity - represents an autonomous AI agent"""
    
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    agent_type = Column(String(100), nullable=False, index=True)  # cart_recovery, payment_recovery, etc.
    description = Column(Text)
    api_key_hash = Column(String(255), nullable=False, unique=True)
    permissions = Column(JSONB, nullable=False, default=dict)  # {"cart_recovery": true, "messaging": true, ...}
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="agents")
    agent_requests = relationship("AgentRequest", back_populates="agent")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, type={self.agent_type})>"
