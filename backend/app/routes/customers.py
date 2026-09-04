"""
Customer Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.agent_request import AgentRequest
from app.models.decision import Decision
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerAnalytics,
    CustomerStats
)

router = APIRouter()


@router.get("/customers", response_model=dict)
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    merchant_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all customers with pagination and filtering.
    
    Query params:
    - skip: Number of records to skip (pagination)
    - limit: Maximum records to return (1-100)
    - merchant_id: Filter by merchant ID
    - search: Search by name, email, or external_id
    """
    query = db.query(Customer)
    
    # Filter by merchant
    if merchant_id:
        try:
            merchant_uuid = uuid.UUID(merchant_id)
            query = query.filter(Customer.merchant_id == merchant_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid merchant_id format")
    
    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.name.ilike(search_pattern)) |
            (Customer.email.ilike(search_pattern)) |
            (Customer.external_id.ilike(search_pattern))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "customers": [
            CustomerResponse(
                id=str(c.id),
                merchant_id=str(c.merchant_id),
                external_id=c.external_id,
                name=c.name,
                email=c.email,
                phone=c.phone,
                consent=c.consent or {},
                custom_metadata=c.custom_metadata or {},
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in customers
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(
    customer: CustomerCreate,
    merchant_id: str = Query(..., description="Merchant ID"),
    db: Session = Depends(get_db)
):
    """
    Create a new customer.
    
    Body: CustomerCreate schema
    Query: merchant_id (required)
    """
    # Validate merchant exists
    try:
        merchant_uuid = uuid.UUID(merchant_id)
        merchant = db.query(Merchant).filter(Merchant.id == merchant_uuid).first()
        if not merchant:
            raise HTTPException(status_code=404, detail="Merchant not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid merchant_id format")
    
    # Check if customer with external_id already exists for this merchant
    existing = db.query(Customer).filter(
        Customer.merchant_id == merchant_uuid,
        Customer.external_id == customer.external_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Customer with external_id '{customer.external_id}' already exists"
        )
    
    # Create customer
    new_customer = Customer(
        merchant_id=merchant_uuid,
        external_id=customer.external_id,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        consent=customer.consent,
        custom_metadata=customer.custom_metadata
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return CustomerResponse(
        id=str(new_customer.id),
        merchant_id=str(new_customer.merchant_id),
        external_id=new_customer.external_id,
        name=new_customer.name,
        email=new_customer.email,
        phone=new_customer.phone,
        consent=new_customer.consent or {},
        custom_metadata=new_customer.custom_metadata or {},
        created_at=new_customer.created_at,
        updated_at=new_customer.updated_at
    )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific customer by ID.
    
    Path: customer_id (UUID)
    """
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer_id format")
    
    customer = db.query(Customer).filter(Customer.id == customer_uuid).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse(
        id=str(customer.id),
        merchant_id=str(customer.merchant_id),
        external_id=customer.external_id,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        consent=customer.consent or {},
        custom_metadata=customer.custom_metadata or {},
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    updates: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a customer.
    
    Path: customer_id (UUID)
    Body: CustomerUpdate schema
    """
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer_id format")
    
    customer = db.query(Customer).filter(Customer.id == customer_uuid).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(customer)
    
    return CustomerResponse(
        id=str(customer.id),
        merchant_id=str(customer.merchant_id),
        external_id=customer.external_id,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        consent=customer.consent or {},
        custom_metadata=customer.custom_metadata or {},
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )


@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a customer.
    
    Path: customer_id (UUID)
    
    Note: This will cascade delete all related records (requests, decisions, etc.)
    """
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer_id format")
    
    customer = db.query(Customer).filter(Customer.id == customer_uuid).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    
    return None


@router.get("/customers/{customer_id}/analytics", response_model=CustomerAnalytics)
def get_customer_analytics(
    customer_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get analytics for a specific customer.
    
    Path: customer_id (UUID)
    Query: days (1-365, default 30) - period for analytics
    
    Returns aggregated statistics about customer interactions.
    """
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer_id format")
    
    customer = db.query(Customer).filter(Customer.id == customer_uuid).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Calculate date range
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all requests for this customer in the period
    requests = db.query(AgentRequest).filter(
        AgentRequest.customer_id == customer_uuid,
        AgentRequest.created_at >= since_date
    ).all()
    
    # Aggregate by intent
    requests_by_intent = {}
    for req in requests:
        intent = req.intent
        requests_by_intent[intent] = requests_by_intent.get(intent, 0) + 1
    
    # Aggregate by channel
    requests_by_channel = {}
    for req in requests:
        channel = req.channel
        requests_by_channel[channel] = requests_by_channel.get(channel, 0) + 1
    
    # Get decisions
    decisions = db.query(Decision).filter(
        Decision.customer_id == customer_uuid,
        Decision.created_at >= since_date
    ).all()
    
    # Aggregate decisions
    decisions_agg = {}
    for dec in decisions:
        dtype = dec.decision_type.lower()
        decisions_agg[dtype] = decisions_agg.get(dtype, 0) + 1
    
    # Calculate total value
    total_value = sum(req.estimated_value or 0 for req in requests)
    
    # Find last contact
    last_contact_at = None
    if requests:
        last_contact_at = max(req.created_at for req in requests)
    
    return CustomerAnalytics(
        customer_id=str(customer.id),
        external_id=customer.external_id,
        name=customer.name,
        total_requests=len(requests),
        requests_by_intent=requests_by_intent,
        requests_by_channel=requests_by_channel,
        decisions=decisions_agg,
        last_contact_at=last_contact_at,
        total_value_engaged=total_value,
        consent_status=customer.consent or {}
    )


@router.get("/customers/stats/summary", response_model=CustomerStats)
def get_customer_stats(
    merchant_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get overall customer statistics.
    
    Query: merchant_id (optional) - filter by merchant
    
    Returns summary statistics across all customers.
    """
    query = db.query(Customer)
    
    # Filter by merchant if specified
    if merchant_id:
        try:
            merchant_uuid = uuid.UUID(merchant_id)
            query = query.filter(Customer.merchant_id == merchant_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid merchant_id format")
    
    # Total customers
    total_customers = query.count()
    
    # Active customers (with requests in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_customers = db.query(distinct(AgentRequest.customer_id)).filter(
        AgentRequest.created_at >= thirty_days_ago
    ).count()
    
    # Opted out customers (global_opt_out = true)
    opted_out = query.filter(
        Customer.consent['global_opt_out'].astext.cast(db.bind.dialect.BOOLEAN) == True
    ).count()
    
    # By merchant
    by_merchant = {}
    merchant_counts = db.query(
        Customer.merchant_id,
        func.count(Customer.id)
    ).group_by(Customer.merchant_id).all()
    
    for merchant_id, count in merchant_counts:
        by_merchant[str(merchant_id)] = count
    
    return CustomerStats(
        total_customers=total_customers,
        active_customers=active_customers,
        opted_out=opted_out,
        by_merchant=by_merchant
    )
