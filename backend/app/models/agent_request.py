"""
Agent Request model
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AgentRequest(Base):
    """Agent Request entity - represents an action request from an agent"""
    
    __tablename__ = "agent_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(String(255), unique=True, nullable=False, index=True)  # For idempotency
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    action_type = Column(String(100), nullable=False)  # SEND_MESSAGE, SEND_EMAIL, etc.
    intent = Column(String(100), nullable=False, index=True)  # CART_RECOVERY, PAYMENT_RECOVERY, etc.
    channel = Column(String(50), nullable=False)  # WHATSAPP, EMAIL, SMS, etc.
    priority = Column(Integer, nullable=False, index=True)  # Agent-suggested priority (can be overridden)
    
    # Business value estimation (NEW - for value-based arbitration)
    estimated_value = Column(Integer)  # Expected business value (e.g., recovery amount in paise)
    urgency = Column(String(50))  # HIGH, MEDIUM, LOW
    
    # Offer details (if any)
    offer = Column(JSONB)  # {"type": "DISCOUNT", "value": 10, "unit": "PERCENT"}
    
    # Message content
    message = Column(Text, nullable=False)
    
    # Request metadata
    expires_at = Column(DateTime)
    metadata = Column(JSONB, default=dict)
    
    # Status
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, evaluated, expired
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="agent_requests")
    agent = relationship("Agent", back_populates="agent_requests")
    customer = relationship("Customer", back_populates="agent_requests")
    decision = relationship("Decision", back_populates="request", uselist=False)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_customer_created', 'customer_id', 'created_at'),
        Index('idx_agent_created', 'agent_id', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AgentRequest(id={self.id}, request_id={self.request_id}, intent={self.intent})>"
