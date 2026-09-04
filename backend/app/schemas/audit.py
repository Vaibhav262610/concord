"""
Audit Log schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Audit log response schema"""
    id: str
    entity_type: str
    entity_id: str
    action: str
    details: Dict[str, Any]
    actor: Optional[str]
    decision_id: Optional[str]
    customer_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs"""
    logs: List[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditLogStats(BaseModel):
    """Audit log statistics"""
    total_logs: int
    by_entity_type: Dict[str, int]
    by_action: Dict[str, int]
    recent_activity_count: int  # Last 24 hours
    
    
class AuditLogTimeline(BaseModel):
    """Timeline view of audit logs for an entity"""
    entity_type: str
    entity_id: str
    logs: List[AuditLogResponse]
    total: int
