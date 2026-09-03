"""
Decision Schemas
Pydantic models for arbitration decisions
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


class DecisionResponse(BaseModel):
    """Response schema for arbitration decision"""
    
    id: UUID = Field(..., description="Decision UUID")
    request_id: UUID = Field(..., description="Agent request ID")
    decision: str = Field(..., description="Decision type: ALLOW, BLOCK, DELAY")
    final_score: Optional[float] = Field(None, description="Combined priority + value score")
    priority_score: Optional[float] = Field(None, description="Priority score (0-100)")
    value_score: Optional[float] = Field(None, description="Business value score (0-100)")
    block_reason: Optional[str] = Field(None, description="Reason if blocked")
    delay_reason: Optional[str] = Field(None, description="Reason if delayed")
    message: str = Field(..., description="Human-readable decision message")
    warnings: Optional[List[str]] = Field(None, description="Warning messages")
    created_at: datetime = Field(..., description="Decision timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "request_id": "123e4567-e89b-12d3-a456-426614174001",
                "decision": "ALLOW",
                "final_score": 78.5,
                "priority_score": 82.0,
                "value_score": 73.0,
                "block_reason": None,
                "delay_reason": None,
                "message": "Request approved - score 78.50",
                "warnings": ["Low attention budget after this contact: 15 points remaining"],
                "created_at": "2026-09-03T10:30:00Z"
            }
        }
    }


class DecisionDetail(BaseModel):
    """Detailed decision breakdown"""
    
    id: UUID
    request_id: UUID
    decision: str
    final_score: Optional[float]
    message: str
    block_reason: Optional[str]
    delay_reason: Optional[str]
    warnings: Optional[List[str]]
    
    # Detailed breakdowns
    customer_state: Dict[str, Any]
    policy_rules: Dict[str, Any]
    checks: Dict[str, Any]
    score_weights: Optional[Dict[str, float]]
    
    created_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "request_id": "123e4567-e89b-12d3-a456-426614174001",
                "decision": "ALLOW",
                "final_score": 78.5,
                "message": "Request approved - score 78.50",
                "block_reason": None,
                "delay_reason": None,
                "warnings": [],
                "customer_state": {
                    "customer_id": "123e4567-e89b-12d3-a456-426614174002",
                    "contacts_today": 1,
                    "attention_budget_remaining": 80
                },
                "policy_rules": {
                    "daily_limit": 3,
                    "max_discount_pct": 30
                },
                "checks": {
                    "consent": {"passed": True},
                    "frequency": {"passed": True},
                    "priority": {"score": 82.0},
                    "business_value": {"score": 73.0}
                },
                "score_weights": {
                    "priority": 0.6,
                    "value": 0.4
                },
                "created_at": "2026-09-03T10:30:00Z"
            }
        }
    }


class DecisionList(BaseModel):
    """List of decisions"""
    
    decisions: List[DecisionResponse]
    total: int
    page: int
    page_size: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "decisions": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "request_id": "123e4567-e89b-12d3-a456-426614174001",
                        "decision": "ALLOW",
                        "final_score": 78.5,
                        "priority_score": 82.0,
                        "value_score": 73.0,
                        "message": "Request approved",
                        "created_at": "2026-09-03T10:30:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20
            }
        }
    }
