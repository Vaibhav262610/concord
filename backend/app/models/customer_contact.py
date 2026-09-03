"""
Customer Contact model
"""

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class CustomerContact(Base):
    """Customer Contact entity - tracks all customer communications"""
    
    __tablename__ = "customer_contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False)
    
    # Contact details
    contact_date = Column(Date, nullable=False, index=True)  # For daily frequency counting
    channel = Column(String(50), nullable=False)  # WHATSAPP, EMAIL, SMS, etc.
    intent = Column(String(100), nullable=False, index=True)  # CART_RECOVERY, PAYMENT_RECOVERY, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="contacts")
    
    # Composite indexes for frequency queries
    __table_args__ = (
        Index('idx_customer_date', 'customer_id', 'contact_date'),
        Index('idx_customer_date_intent', 'customer_id', 'contact_date', 'intent'),
    )
    
    def __repr__(self):
        return f"<CustomerContact(id={self.id}, customer_id={self.customer_id}, date={self.contact_date})>"
