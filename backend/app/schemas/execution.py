"""
Execution Schemas
Pydantic models for execution and delivery tracking
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID


class ExecutionResponse(BaseModel):
    """Response schema for execution"""
    
    id: UUID = Field(..., description="Execution UUID")
    request_id: UUID = Field(..., description="Agent request ID")
    decision_id: UUID = Field(..., description="Decision ID")
    status: str = Field(..., description="Execution status: queued, executing, sent, delivered, failed")
    channel: Optional[str] = Field(None, description="Communication channel")
    scheduled_for: datetime = Field(..., description="When execution is/was scheduled")
    executed_at: Optional[datetime] = Field(None, description="When execution completed")
    retry_count: int = Field(0, description="Number of retry attempts")
    last_error: Optional[str] = Field(None, description="Last error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Execution metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "request_id": "123e4567-e89b-12d3-a456-426614174001",
                "decision_id": "123e4567-e89b-12d3-a456-426614174002",
                "status": "sent",
                "channel": "EMAIL",
                "scheduled_for": "2026-09-03T12:00:00Z",
                "executed_at": "2026-09-03T12:00:05Z",
                "retry_count": 0,
                "last_error": None,
                "metadata": {
                    "provider_id": "email_abc123",
                    "delivery_status": "delivered"
                }
            }
        }
    }


class DeliveryStatusResponse(BaseModel):
    """Response schema for delivery status"""
    
    execution_id: UUID = Field(..., description="Execution UUID")
    status: str = Field(..., description="Delivery status")
    delivery_status: Optional[str] = Field(None, description="Detailed delivery status")
    provider_id: Optional[str] = Field(None, description="Provider message ID")
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    opened_at: Optional[datetime] = Field(None, description="Open timestamp")
    clicked_at: Optional[datetime] = Field(None, description="Click timestamp")
    last_error: Optional[str] = Field(None, description="Error message if applicable")
    status_history: List[Dict[str, Any]] = Field(default_factory=list, description="Status change history")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "sent",
                "delivery_status": "delivered",
                "provider_id": "email_abc123",
                "executed_at": "2026-09-03T12:00:00Z",
                "delivered_at": "2026-09-03T12:00:05Z",
                "opened_at": "2026-09-03T12:15:00Z",
                "clicked_at": None,
                "last_error": None,
                "status_history": [
                    {"status": "sent", "timestamp": "2026-09-03T12:00:00Z"},
                    {"status": "delivered", "timestamp": "2026-09-03T12:00:05Z"},
                    {"status": "opened", "timestamp": "2026-09-03T12:15:00Z"}
                ]
            }
        }
    }


class ExecutionListItem(BaseModel):
    """Item in execution list"""
    
    id: UUID
    request_id: UUID
    status: str
    channel: Optional[str]
    scheduled_for: datetime
    executed_at: Optional[datetime]
    delivery_status: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }


class ExecutionListResponse(BaseModel):
    """Response for list of executions"""
    
    executions: List[ExecutionListItem]
    total: int
    page: int
    page_size: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "executions": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "request_id": "123e4567-e89b-12d3-a456-426614174001",
                        "status": "sent",
                        "channel": "EMAIL",
                        "scheduled_for": "2026-09-03T12:00:00Z",
                        "executed_at": "2026-09-03T12:00:05Z",
                        "delivery_status": "delivered"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20
            }
        }
    }


class DeliveryMetricsResponse(BaseModel):
    """Response for delivery metrics"""
    
    total_executions: int
    sent: int
    delivered: int
    failed: int
    bounced: int
    delivery_rate: float = Field(..., description="Delivery rate percentage")
    failure_rate: float = Field(..., description="Failure rate percentage")
    bounce_rate: float = Field(..., description="Bounce rate percentage")
    start_date: datetime
    end_date: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_executions": 100,
                "sent": 95,
                "delivered": 90,
                "failed": 5,
                "bounced": 5,
                "delivery_rate": 94.7,
                "failure_rate": 5.3,
                "bounce_rate": 5.3,
                "start_date": "2026-09-01T00:00:00Z",
                "end_date": "2026-09-03T23:59:59Z"
            }
        }
    }


class WebhookPayload(BaseModel):
    """Generic webhook payload"""
    
    execution_id: UUID
    event: str
    message_id: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "event": "delivered",
                "message_id": "email_abc123",
                "status": "delivered",
                "timestamp": "2026-09-03T12:00:05Z",
                "error": None,
                "metadata": {}
            }
        }
    }
