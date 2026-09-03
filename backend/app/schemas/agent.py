"""
Pydantic schemas for agents
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class AgentCreate(BaseModel):
    """Schema for creating/registering a new agent"""
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    agent_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of agent (cart_recovery, payment_recovery, etc.)"
    )
    description: Optional[str] = Field(None, max_length=1000, description="Agent description")
    permissions: Dict[str, bool] = Field(
        ...,
        description="Agent permissions (e.g., {'messaging': true, 'discounts': true})"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Cart Recovery Agent",
                "agent_type": "cart_recovery",
                "description": "Handles abandoned cart recovery with automated messaging",
                "permissions": {
                    "messaging": True,
                    "discounts": True,
                    "high_value_discounts": False,
                    "refunds": False
                }
            }
        }


class AgentResponse(BaseModel):
    """Response after agent registration"""
    id: str
    name: str
    agent_type: str
    api_key: str = Field(..., description="Generated API key (save this - won't be shown again)")
    permissions: Dict[str, bool]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Cart Recovery Agent",
                "agent_type": "cart_recovery",
                "api_key": "sk_live_abc123xyz789...",
                "permissions": {
                    "messaging": True,
                    "discounts": True
                },
                "is_active": True,
                "created_at": "2026-09-03T10:00:00Z"
            }
        }


class AgentListItem(BaseModel):
    """Item in agent list"""
    id: str
    name: str
    agent_type: str
    is_active: bool
    permissions: Dict[str, bool]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Response for list of agents"""
    agents: list[AgentListItem]
    total: int
