"""
Pydantic schemas for agent action requests
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """Valid action types"""
    SEND_MESSAGE = "SEND_MESSAGE"
    SEND_EMAIL = "SEND_EMAIL"
    SEND_SMS = "SEND_SMS"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"


class Intent(str, Enum):
    """Valid intent types"""
    CART_RECOVERY = "CART_RECOVERY"
    PAYMENT_RECOVERY = "PAYMENT_RECOVERY"
    SUBSCRIPTION_RECOVERY = "SUBSCRIPTION_RECOVERY"
    UPSELL = "UPSELL"
    PROMOTION = "PROMOTION"
    WIN_BACK = "WIN_BACK"
    GENERAL = "GENERAL"


class Channel(str, Enum):
    """Valid communication channels"""
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"


class Urgency(str, Enum):
    """Urgency levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class OfferType(str, Enum):
    """Valid offer types"""
    DISCOUNT = "DISCOUNT"
    CASHBACK = "CASHBACK"
    FREE_SHIPPING = "FREE_SHIPPING"
    BUY_ONE_GET_ONE = "BUY_ONE_GET_ONE"
    COUPON = "COUPON"


class OfferUnit(str, Enum):
    """Offer value units"""
    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"


class OfferSchema(BaseModel):
    """Offer details in a request"""
    type: OfferType
    value: float = Field(..., gt=0, description="Offer value (percentage or amount)")
    unit: OfferUnit
    max_amount: Optional[float] = Field(None, description="Maximum discount amount in paise")
    min_order_value: Optional[float] = Field(None, description="Minimum order value required in paise")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "DISCOUNT",
                "value": 10,
                "unit": "PERCENT",
                "max_amount": 100000,
                "min_order_value": 50000
            }
        }


class AgentActionRequest(BaseModel):
    """
    Schema for agent action request submission
    This is what agents send to CONCORD
    """
    request_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique idempotency key for this request"
    )
    customer_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Customer identifier (will be resolved to CONCORD customer)"
    )
    action: ActionType = Field(..., description="Type of action to perform")
    intent: Intent = Field(..., description="Business intent of this action")
    channel: Channel = Field(..., description="Communication channel")
    priority: int = Field(
        ...,
        ge=0,
        le=100,
        description="Agent-suggested priority (0-100, can be overridden by policy)"
    )
    estimated_value: Optional[int] = Field(
        None,
        ge=0,
        description="Expected business value in paise (for value-based arbitration)"
    )
    urgency: Optional[Urgency] = Field(
        None,
        description="Urgency level (affects arbitration)"
    )
    offer: Optional[OfferSchema] = Field(None, description="Offer details if any")
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content to send to customer"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="When this request expires (ISO 8601 format)"
    )
    custom_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata for this request"
    )
    
    @field_validator('expires_at')
    @classmethod
    def validate_expiry(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('expires_at must be in the future')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_cart_20260903_001",
                "customer_id": "cust_456",
                "action": "SEND_MESSAGE",
                "intent": "CART_RECOVERY",
                "channel": "WHATSAPP",
                "priority": 70,
                "estimated_value": 85000,
                "urgency": "MEDIUM",
                "offer": {
                    "type": "DISCOUNT",
                    "value": 10,
                    "unit": "PERCENT"
                },
                "message": "Complete your purchase and get 10% off!",
                "expires_at": "2026-09-03T18:00:00Z"
            }
        }


class AgentActionResponse(BaseModel):
    """Response after submitting an action request"""
    id: str
    request_id: str
    status: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "request_id": "req_cart_20260903_001",
                "status": "pending",
                "message": "Request received and queued for arbitration",
                "created_at": "2026-09-03T10:41:02Z"
            }
        }


class AgentActionListItem(BaseModel):
    """Item in action request list"""
    id: str
    request_id: str
    customer_id: str
    agent_id: str
    intent: str
    channel: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentActionListResponse(BaseModel):
    """Response for list of action requests"""
    requests: list[AgentActionListItem]
    total: int
    limit: int
    offset: int


class AgentActionDetail(BaseModel):
    """Detailed action request information"""
    id: str
    request_id: str
    customer_id: str
    agent_id: str
    merchant_id: str
    action_type: str
    intent: str
    channel: str
    priority: int
    estimated_value: Optional[int]
    urgency: Optional[str]
    offer: Optional[Dict[str, Any]]
    message: str
    expires_at: Optional[datetime]
    custom_metadata: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
