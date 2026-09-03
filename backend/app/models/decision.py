"""
Decision model
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Decision(Base):
    """Decision entity - represents Concord's arbitration decision"""
    
    __tablename__ = "decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("agent_requests.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Decision outcome
    decision = Column(String(50), nullable=False, index=True)  # ALLOW, BLOCK, DELAY, MERGE
    reason_code = Column(String(100), nullable=False, index=True)  # CONSENT_DENIED, FREQUENCY_LIMIT_EXCEEDED, etc.
    reason = Column(Text, nullable=False)  # Human-readable explanation
    
    # Policy references
    policy_ids = Column(JSONB, default=list)  # List of policy IDs that influenced this decision
    
    # Conflict information
    conflicting_requests = Column(JSONB, default=list)  # List of conflicting request IDs
    
    # Merge information (if MERGE decision)
    merged_with = Column(JSONB)  # List of request IDs merged together
    merged_message = Column(Text)  # Final merged message
    
    # Delay information (if DELAY decision)
    scheduled_at = Column(DateTime)  # When to retry the action
    delay_reason = Column(String(255))
    
    # Execution status
    executed = Column(String(50), default="pending")  # pending, executed, failed, cancelled
    executed_at = Column(DateTime)
    
    # Performance metrics
    evaluation_duration_ms = Column(Integer)  # How long the arbitration took
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    request = relationship("AgentRequest", back_populates="decision")
    customer = relationship("Customer", back_populates="decisions")
    audit_logs = relationship("AuditLog", back_populates="decision", cascade="all, delete-orphan")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_decision_created', 'decision', 'created_at'),
        Index('idx_customer_decision', 'customer_id', 'decision'),
    )
    
    def __repr__(self):
        return f"<Decision(id={self.id}, decision={self.decision}, reason_code={self.reason_code})>"
