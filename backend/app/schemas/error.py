"""
Error response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    request_id: Optional[str] = Field(None, description="Request ID if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "AGENT_NOT_AUTHORIZED",
                "message": "Agent does not have permission to perform this action",
                "request_id": "req_123",
                "timestamp": "2026-09-03T10:41:03Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail
