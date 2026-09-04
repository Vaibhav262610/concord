"""
Customer schemas
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime


class CustomerBase(BaseModel):
    """Base customer schema"""
    external_id: str = Field(..., description="Merchant's customer ID")
    name: Optional[str] = Field(None, description="Customer name")
    email: Optional[EmailStr] = Field(None, description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    consent: Dict[str, Any] = Field(
        default_factory=lambda: {
            "marketing": True,
            "transactional": True,
            "global_opt_out": False
        },
        description="Consent settings"
    )
    custom_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional customer data"
    )


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    consent: Optional[Dict[str, Any]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: str
    merchant_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerAnalytics(BaseModel):
    """Customer analytics schema"""
    customer_id: str
    external_id: str
    name: Optional[str]
    total_requests: int
    requests_by_intent: Dict[str, int]
    requests_by_channel: Dict[str, int]
    decisions: Dict[str, int]  # allow, block, delay, merge counts
    last_contact_at: Optional[datetime]
    total_value_engaged: int  # Total estimated value across all requests
    consent_status: Dict[str, Any]
    
    class Config:
        from_attributes = True


class CustomerStats(BaseModel):
    """Customer statistics summary"""
    total_customers: int
    active_customers: int  # Customers with requests in last 30 days
    opted_out: int
    by_merchant: Dict[str, int]
