"""
Audit Log model
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AuditLog(Base):
    """Audit Log entity - comprehensive audit trail for all actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Entity being audited
    entity_type = Column(String(100), nullable=False, index=True)  # agent_request, decision, policy, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Action performed
    action = Column(String(100), nullable=False, index=True)  # CREATED, EVALUATED, ALLOWED, BLOCKED, etc.
    
    # Details
    details = Column(JSONB, nullable=False, default=dict)
    # Example: {"previous_state": {...}, "new_state": {...}, "reason": "..."}
    
    # Actor
    actor = Column(String(255))  # Who/what performed the action (agent_id, system, user_id, etc.)
    
    # Foreign keys (optional, for easier querying)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    decision = relationship("Decision", back_populates="audit_logs")
    
    # Composite indexes for timeline queries
    __table_args__ = (
        Index('idx_entity_created', 'entity_type', 'entity_id', 'created_at'),
        Index('idx_customer_created', 'customer_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, entity_type={self.entity_type}, action={self.action})>"
