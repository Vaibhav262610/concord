"""
Policy model
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Policy(Base):
    """Policy entity - represents merchant policies for arbitration"""
    
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_type = Column(String(100), nullable=False, index=True)  # frequency, discount, priority, consent
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    
    # Policy configuration
    config = Column(JSONB, nullable=False, default=dict)
    # Examples:
    # - frequency: {"max_daily_contacts": 3, "intent_specific": {"marketing": 2, "transactional": 5}}
    # - discount: {"max_discount_percent": 10, "max_discount_amount": 1000}
    # - priority: {"payment_recovery": 100, "subscription": 90, "cart_recovery": 70, "upsell": 30}
    # - consent: {"require_marketing_consent": true, "honor_opt_out": true}
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="policies")
    
    def __repr__(self):
        return f"<Policy(id={self.id}, type={self.policy_type}, name={self.name})>"
