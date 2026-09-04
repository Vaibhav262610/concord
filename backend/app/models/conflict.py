"""
Conflict model - tracks detected conflicts between agents
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Conflict(Base):
    """Conflict entity - tracks when multiple agents target the same customer"""
    
    __tablename__ = "conflicts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    
    # Conflicting requests
    request_ids = Column(JSON, nullable=False)  # List of conflicting request IDs
    agent_ids = Column(JSON, nullable=False)  # List of agent IDs involved
    
    # Conflict details
    conflict_type = Column(String(50), nullable=False, index=True)  # SIMULTANEOUS, RAPID_SUCCESSION, CHANNEL_OVERLAP
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Resolution
    status = Column(String(50), nullable=False, default="detected", index=True)  # detected, analyzing, resolved, merged, suppressed
    resolution_strategy = Column(String(50))  # MERGE, SUPPRESS_LOWER, DELAY_CONFLICTING, MANUAL
    merged_request_id = Column(UUID(as_uuid=True), ForeignKey("agent_requests.id"))  # If merged
    
    # Metadata
    conflict_details = Column(JSON)  # Detailed analysis
    resolution_metadata = Column(JSON)  # Resolution details
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_conflict_customer_status', 'customer_id', 'status'),
        Index('idx_conflict_detected_at', 'detected_at'),
    )
    
    def __repr__(self):
        return f"<Conflict(id={self.id}, customer_id={self.customer_id}, type={self.conflict_type}, status={self.status})>"
