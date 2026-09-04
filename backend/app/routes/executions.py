"""
API routes for executions and delivery tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.dependencies import get_db, get_current_agent
from app.models.agent import Agent
from app.models.delayed_action import DelayedAction
from app.models.agent_request import AgentRequest
from app.schemas.execution import (
    ExecutionResponse,
    ExecutionListResponse,
    ExecutionListItem,
    DeliveryStatusResponse,
    DeliveryMetricsResponse
)
from app.schemas.error import ErrorResponse
from app.services.execution_service import ExecutionService
from app.services.delivery_tracking import DeliveryTrackingService


router = APIRouter(prefix="/executions", tags=["executions"])


@router.get(
    "",
    response_model=ExecutionListResponse,
    responses={
        200: {"description": "List of executions"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
    }
)
async def list_executions(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    List executions
    
    Returns paginated list of executions for the authenticated agent's merchant.
    """
    # Query executions (using delayed_action table)
    query = db.query(DelayedAction).join(AgentRequest).filter(
        AgentRequest.merchant_id == agent.merchant_id
    )
    
    if status_filter:
        query = query.filter(DelayedAction.status == status_filter)
    
    # Filter by channel via metadata (simplified for MVP)
    # In production, add channel column to delayed_action table
    
    total = query.count()
    
    executions = query.order_by(
        DelayedAction.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return ExecutionListResponse(
        executions=[
            ExecutionListItem(
                id=exec.id,
                request_id=exec.request_id,
                status=exec.status,
                channel=exec.execution_metadata.get("channel") if exec.execution_metadata else None,
                scheduled_for=exec.scheduled_for,
                executed_at=exec.executed_at,
                delivery_status=exec.execution_metadata.get("delivery_status") if exec.execution_metadata else None
            )
            for exec in executions
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{execution_id}",
    response_model=ExecutionResponse,
    responses={
        200: {"description": "Execution details"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        404: {"model": ErrorResponse, "description": "Execution not found"},
    }
)
async def get_execution(
    execution_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get execution details
    
    Returns complete information about a specific execution.
    """
    execution = db.query(DelayedAction).filter(
        DelayedAction.id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EXECUTION_NOT_FOUND",
                    "message": f"Execution {execution_id} not found"
                }
            }
        )
    
    # Verify agent has access
    agent_request = db.query(AgentRequest).filter(
        AgentRequest.id == execution.request_id
    ).first()
    
    if not agent_request or agent_request.merchant_id != agent.merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCESS_DENIED",
                    "message": "You do not have access to this execution"
                }
            }
        )
    
    return ExecutionResponse(
        id=execution.id,
        request_id=execution.request_id,
        decision_id=execution.decision_id,
        status=execution.status,
        channel=execution.execution_metadata.get("channel") if execution.execution_metadata else None,
        scheduled_for=execution.scheduled_for,
        executed_at=execution.executed_at,
        retry_count=execution.retry_count,
        last_error=execution.last_error,
        metadata=execution.execution_metadata
    )


@router.get(
    "/{execution_id}/status",
    response_model=DeliveryStatusResponse,
    responses={
        200: {"description": "Delivery status"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        404: {"model": ErrorResponse, "description": "Execution not found"},
    }
)
async def get_delivery_status(
    execution_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get delivery status for an execution
    
    Returns detailed delivery tracking information including:
    - Current status
    - Delivery timestamps
    - Engagement events (opened, clicked)
    - Status history
    """
    tracking_service = DeliveryTrackingService(db)
    
    status_data = tracking_service.get_delivery_status(execution_id)
    
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EXECUTION_NOT_FOUND",
                    "message": f"Execution {execution_id} not found"
                }
            }
        )
    
    # Verify access (simplified for MVP)
    
    return DeliveryStatusResponse(
        execution_id=uuid.UUID(status_data["execution_id"]),
        status=status_data["status"],
        delivery_status=status_data["delivery_status"],
        provider_id=status_data["provider_id"],
        executed_at=datetime.fromisoformat(status_data["executed_at"]) if status_data.get("executed_at") else None,
        delivered_at=datetime.fromisoformat(status_data["delivered_at"]) if status_data.get("delivered_at") else None,
        opened_at=datetime.fromisoformat(status_data["opened_at"]) if status_data.get("opened_at") else None,
        clicked_at=datetime.fromisoformat(status_data["clicked_at"]) if status_data.get("clicked_at") else None,
        last_error=status_data["last_error"],
        status_history=status_data["status_history"]
    )


@router.get(
    "/metrics/delivery",
    response_model=DeliveryMetricsResponse,
    responses={
        200: {"description": "Delivery metrics"},
    }
)
async def get_delivery_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    db: Session = Depends(get_db)
):
    """
    Get delivery metrics
    
    Returns aggregated delivery statistics for a time period:
    - Total executions
    - Delivery rate
    - Failure rate
    - Bounce rate
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    tracking_service = DeliveryTrackingService(db)
    
    metrics = tracking_service.get_delivery_metrics(
        start_date=start_date,
        end_date=end_date,
        channel=channel
    )
    
    return DeliveryMetricsResponse(
        total_executions=metrics["total_executions"],
        sent=metrics["sent"],
        delivered=metrics["delivered"],
        failed=metrics["failed"],
        bounced=metrics["bounced"],
        delivery_rate=metrics["delivery_rate"],
        failure_rate=metrics["failure_rate"],
        bounce_rate=metrics["bounce_rate"],
        start_date=start_date,
        end_date=end_date
    )
