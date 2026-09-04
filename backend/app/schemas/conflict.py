"""
Conflict schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ConflictResponse(BaseModel):
    """Single conflict response"""
    id: UUID
    customer_id: str
    request_ids: List[str]
    agent_ids: List[str]
    conflict_type: str
    severity: str
    status: str
    resolution_strategy: Optional[str] = None
    merged_request_id: Optional[UUID] = None
    conflict_details: Optional[Dict[str, Any]] = None
    resolution_metadata: Optional[Dict[str, Any]] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConflictListResponse(BaseModel):
    """Paginated list of conflicts"""
    conflicts: List[ConflictResponse]
    total: int
    skip: int
    limit: int


class MergeRecommendationResponse(BaseModel):
    """Merge recommendation for a conflict"""
    conflict_id: str
    conflict_type: str
    severity: str
    request_count: int
    requests: List[Dict[str, Any]]
    recommended_strategy: str
    alternative_strategies: List[str]
    likely_winner: str
    reason: str


class MergeRequest(BaseModel):
    """Request to merge a conflict"""
    strategy: Optional[str] = Field(
        None,
        description="Merge strategy to use (auto-select if not provided)"
    )


class MergeResult(BaseModel):
    """Result of a merge operation"""
    success: bool
    conflict_id: str
    winning_request_id: str
    strategy_used: str
    suppressed_count: int
    message: str
