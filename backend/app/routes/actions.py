"""
API routes for agent action requests
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.dependencies import get_db, get_current_agent
from app.models.agent import Agent
from app.schemas.agent_request import (
    AgentActionRequest,
    AgentActionResponse,
    AgentActionListResponse,
    AgentActionListItem,
    AgentActionDetail
)
from app.schemas.decision import DecisionResponse
from app.schemas.error import ErrorResponse
from app.services.gateway import GatewayService, ValidationError
from app.services.decision_service import DecisionService


router = APIRouter(prefix="/actions", tags=["actions"])


@router.post(
    "",
    response_model=AgentActionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Request accepted and queued for arbitration"},
        200: {"description": "Duplicate request (idempotent response)"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    }
)
async def submit_action_request(
    request: AgentActionRequest,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Submit an agent action request for arbitration
    
    This is the main entry point for all agent actions. The request will be:
    1. Authenticated (via API key)
    2. Validated (permissions, offer limits, expiry)
    3. Checked for idempotency (duplicate request_id)
    4. Persisted to database
    5. Run through arbitration engine (ALLOW/BLOCK/DELAY decision)
    
    Returns HTTP 201 for new requests, HTTP 200 for duplicate requests (idempotent).
    """
    gateway = GatewayService(db)
    decision_service = DecisionService(db)
    
    try:
        # Process request through gateway (includes arbitration)
        agent_request, is_duplicate, decision = gateway.process_action_request(agent, request)
        
        # Build response
        response_data = {
            "id": str(agent_request.id),
            "request_id": agent_request.request_id,
            "status": agent_request.status,
            "created_at": agent_request.created_at
        }
        
        # Add decision info if available
        if decision:
            response_data["decision"] = decision_service.to_response(decision).model_dump()
            response_data["message"] = decision.message
        else:
            response_data["message"] = "Request received and queued for arbitration" if not is_duplicate else "Duplicate request (idempotent)"
        
        # Return appropriate status code
        response_status = status.HTTP_200_OK if is_duplicate else status.HTTP_201_CREATED
        
        return response_data
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "request_id": request.request_id
                }
            }
        )
    except Exception as e:
        # Log unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request.request_id
                }
            }
        )


@router.get(
    "",
    response_model=AgentActionListResponse,
    responses={
        200: {"description": "List of action requests"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
    }
)
async def list_action_requests(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    List action requests
    
    Returns paginated list of action requests for the authenticated agent's merchant.
    Can be filtered by customer ID and status.
    """
    gateway = GatewayService(db)
    
    # Convert customer_id string to UUID if provided
    customer_uuid = None
    if customer_id:
        try:
            # First try to find customer by external_id
            from app.models.customer import Customer
            customer = db.query(Customer).filter(
                Customer.merchant_id == agent.merchant_id,
                Customer.external_id == customer_id
            ).first()
            if customer:
                customer_uuid = customer.id
        except Exception:
            pass
    
    requests, total = gateway.get_agent_requests(
        merchant_id=agent.merchant_id,
        customer_id=customer_uuid,
        agent_id=agent.id,  # Only show this agent's requests
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return AgentActionListResponse(
        requests=[
            AgentActionListItem(
                id=str(req.id),
                request_id=req.request_id,
                customer_id=str(req.customer_id),
                agent_id=str(req.agent_id),
                intent=req.intent,
                channel=req.channel,
                status=req.status,
                created_at=req.created_at
            )
            for req in requests
        ],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{request_id}",
    response_model=AgentActionDetail,
    responses={
        200: {"description": "Action request details"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        404: {"model": ErrorResponse, "description": "Request not found"},
    }
)
async def get_action_request(
    request_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific action request
    
    Returns complete details of the action request including offer, message, and status.
    """
    gateway = GatewayService(db)
    
    agent_request = gateway.get_agent_request_by_id(request_id, agent.merchant_id)
    
    if not agent_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "REQUEST_NOT_FOUND",
                    "message": f"Action request {request_id} not found"
                }
            }
        )
    
    # Verify agent has access to this request
    if agent_request.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCESS_DENIED",
                    "message": "You do not have access to this request"
                }
            }
        )
    
    return AgentActionDetail(
        id=str(agent_request.id),
        request_id=agent_request.request_id,
        customer_id=str(agent_request.customer_id),
        agent_id=str(agent_request.agent_id),
        merchant_id=str(agent_request.merchant_id),
        action_type=agent_request.action_type,
        intent=agent_request.intent,
        channel=agent_request.channel,
        priority=agent_request.priority,
        estimated_value=agent_request.estimated_value,
        urgency=agent_request.urgency,
        offer=agent_request.offer,
        message=agent_request.message,
        expires_at=agent_request.expires_at,
        custom_metadata=agent_request.custom_metadata,
        status=agent_request.status,
        created_at=agent_request.created_at
    )
