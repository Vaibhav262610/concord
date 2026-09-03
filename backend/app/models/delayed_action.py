"""
Delayed Action model
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class DelayedAction(Base):
    """Delayed Action entity - tracks actions scheduled for later execution"""
    
    __tablename__ = "delayed_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("agent_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False, index=True)  # When to retry
    expires_at = Column(DateTime, nullable=False, index=True)  # When to give up
    
    # Retry tracking
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, processed, expired, cancelled
    
    # Reason for delay
    delay_reason = Column(String(255), nullable=False)
    
    # Result (if processed)
    result = Column(String(50))  # success, failed
    result_message = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # Composite indexes for worker queries
    __table_args__ = (
        Index('idx_scheduled_status', 'scheduled_at', 'status'),
        Index('idx_expires_status', 'expires_at', 'status'),
    )
    
    def __repr__(self):
        return f"<DelayedAction(id={self.id}, scheduled_at={self.scheduled_at}, status={self.status})>"
