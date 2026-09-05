"""
API routes for arbitration decisions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.dependencies import get_db, get_current_agent
from app.models.agent import Agent
from app.schemas.decision import DecisionResponse, DecisionDetail, DecisionList
from app.schemas.error import ErrorResponse
from app.services.decision_service import DecisionService


router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get(
    "",
    response_model=DecisionList,
    responses={
        200: {"description": "List of arbitration decisions"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
    }
)
async def list_decisions(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    decision: Optional[str] = Query(None, description="Filter by decision type (ALLOW, BLOCK, DELAY)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # agent: Agent = Depends(get_current_agent),  # Removed for demo
    db: Session = Depends(get_db)
):
    """
    List arbitration decisions
    
    Returns paginated list of decisions for the authenticated agent's merchant.
    Can be filtered by customer ID and decision type.
    """
    decision_service = DecisionService(db)
    
    # Convert customer_id string to UUID if provided
    customer_uuid = None
    if customer_id:
        try:
            from app.models.customer import Customer
            # Show all customers for demo
            customer = db.query(Customer).filter(
                Customer.external_id == customer_id
            ).first()
            if customer:
                customer_uuid = customer.id
        except Exception:
            pass
    
    decisions, total = decision_service.get_decisions(
        customer_id=customer_uuid,
        decision_type=decision,
        page=page,
        page_size=page_size
    )
    
    return decision_service.to_list(decisions, total, page, page_size)


@router.get(
    "/{decision_id}",
    response_model=DecisionDetail,
    responses={
        200: {"description": "Decision details with full breakdown"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        404: {"model": ErrorResponse, "description": "Decision not found"},
    }
)
async def get_decision(
    decision_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific arbitration decision
    
    Returns complete breakdown including:
    - Customer state at time of decision
    - Policy rules applied
    - All check results (consent, frequency, priority, value)
    - Score calculations and weights
    """
    decision_service = DecisionService(db)
    
    decision = decision_service.get_decision(decision_id)
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "DECISION_NOT_FOUND",
                    "message": f"Decision {decision_id} not found"
                }
            }
        )
    
    # Verify agent has access (check merchant through request)
    from app.models.agent_request import AgentRequest
    agent_request = db.query(AgentRequest).filter(
        AgentRequest.id == decision.request_id
    ).first()
    
    if not agent_request or agent_request.merchant_id != agent.merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCESS_DENIED",
                    "message": "You do not have access to this decision"
                }
            }
        )
    
    return decision_service.to_detail(decision)


@router.get(
    "/request/{request_id}",
    response_model=DecisionDetail,
    responses={
        200: {"description": "Decision for specific request"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        404: {"model": ErrorResponse, "description": "Decision not found"},
    }
)
async def get_decision_by_request(
    request_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get arbitration decision for a specific request
    
    Convenience endpoint to get decision by request ID instead of decision ID.
    """
    decision_service = DecisionService(db)
    
    decision = decision_service.get_decision_by_request(request_id)
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "DECISION_NOT_FOUND",
                    "message": f"No decision found for request {request_id}"
                }
            }
        )
    
    # Verify agent has access
    from app.models.agent_request import AgentRequest
    agent_request = db.query(AgentRequest).filter(
        AgentRequest.id == request_id
    ).first()
    
    if not agent_request or agent_request.merchant_id != agent.merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCESS_DENIED",
                    "message": "You do not have access to this decision"
                }
            }
        )
    
    return decision_service.to_detail(decision)
