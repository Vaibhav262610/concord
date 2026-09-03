"""
Customer model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Customer(Base):
    """Customer entity - represents a merchant's customer"""
    
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=False, index=True)  # Merchant's customer ID
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    
    # Consent settings
    consent = Column(JSONB, nullable=False, default=dict)
    # Example: {"marketing": true, "transactional": true, "global_opt_out": false}
    
    # Metadata
    metadata = Column(JSONB, default=dict)  # Additional customer data
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="customers")
    agent_requests = relationship("AgentRequest", back_populates="customer")
    decisions = relationship("Decision", back_populates="customer")
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name}, external_id={self.external_id})>"
