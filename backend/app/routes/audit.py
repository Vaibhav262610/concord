"""
Audit Trail API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogStats,
    AuditLogTimeline
)

router = APIRouter()


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    customer_id: Optional[str] = None,
    decision_id: Optional[str] = None,
    actor: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List audit logs with filtering.
    
    Query params:
    - skip: Pagination offset
    - limit: Max records (1-200)
    - entity_type: Filter by entity type (agent_request, decision, etc.)
    - action: Filter by action (CREATED, EVALUATED, ALLOWED, etc.)
    - customer_id: Filter by customer UUID
    - decision_id: Filter by decision UUID
    - actor: Filter by actor
    - start_date: ISO format date (inclusive)
    - end_date: ISO format date (inclusive)
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if customer_id:
        try:
            customer_uuid = uuid.UUID(customer_id)
            query = query.filter(AuditLog.customer_id == customer_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid customer_id format")
    
    if decision_id:
        try:
            decision_uuid = uuid.UUID(decision_id)
            query = query.filter(AuditLog.decision_id == decision_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid decision_id format")
    
    if actor:
        query = query.filter(AuditLog.actor == actor)
    
    # Date range filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    # Get total count
    total = query.count()
    
    # Order by most recent first and paginate
    logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        logs=[
            AuditLogResponse(
                id=str(log.id),
                entity_type=log.entity_type,
                entity_id=str(log.entity_id),
                action=log.action,
                details=log.details or {},
                actor=log.actor,
                decision_id=str(log.decision_id) if log.decision_id else None,
                customer_id=str(log.customer_id) if log.customer_id else None,
                created_at=log.created_at
            )
            for log in logs
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific audit log entry.
    
    Path: log_id (UUID)
    """
    try:
        log_uuid = uuid.UUID(log_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log_id format")
    
    log = db.query(AuditLog).filter(AuditLog.id == log_uuid).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return AuditLogResponse(
        id=str(log.id),
        entity_type=log.entity_type,
        entity_id=str(log.entity_id),
        action=log.action,
        details=log.details or {},
        actor=log.actor,
        decision_id=str(log.decision_id) if log.decision_id else None,
        customer_id=str(log.customer_id) if log.customer_id else None,
        created_at=log.created_at
    )


@router.get("/audit-logs/entity/{entity_type}/{entity_id}", response_model=AuditLogTimeline)
def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get audit timeline for a specific entity.
    
    Path:
    - entity_type: Type of entity (agent_request, decision, etc.)
    - entity_id: UUID of entity
    
    Query:
    - limit: Max records (1-500)
    
    Returns chronological audit trail for the entity.
    """
    try:
        entity_uuid = uuid.UUID(entity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity_id format")
    
    # Query logs for this entity
    query = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_uuid
    )
    
    total = query.count()
    
    # Order by creation time (chronological)
    logs = query.order_by(AuditLog.created_at).limit(limit).all()
    
    return AuditLogTimeline(
        entity_type=entity_type,
        entity_id=entity_id,
        logs=[
            AuditLogResponse(
                id=str(log.id),
                entity_type=log.entity_type,
                entity_id=str(log.entity_id),
                action=log.action,
                details=log.details or {},
                actor=log.actor,
                decision_id=str(log.decision_id) if log.decision_id else None,
                customer_id=str(log.customer_id) if log.customer_id else None,
                created_at=log.created_at
            )
            for log in logs
        ],
        total=total
    )


@router.get("/audit-logs/customer/{customer_id}/timeline", response_model=AuditLogListResponse)
def get_customer_timeline(
    customer_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get audit timeline for a customer.
    
    Path: customer_id (UUID)
    Query: skip, limit for pagination
    
    Returns all audit logs related to a customer.
    """
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer_id format")
    
    query = db.query(AuditLog).filter(AuditLog.customer_id == customer_uuid)
    
    total = query.count()
    
    logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        logs=[
            AuditLogResponse(
                id=str(log.id),
                entity_type=log.entity_type,
                entity_id=str(log.entity_id),
                action=log.action,
                details=log.details or {},
                actor=log.actor,
                decision_id=str(log.decision_id) if log.decision_id else None,
                customer_id=str(log.customer_id) if log.customer_id else None,
                created_at=log.created_at
            )
            for log in logs
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/audit-logs/stats/summary", response_model=AuditLogStats)
def get_audit_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get audit log statistics.
    
    Query: days (1-365) - period to analyze
    
    Returns aggregated statistics about audit activity.
    """
    # Calculate date range
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Total logs in period
    total_logs = db.query(AuditLog).filter(AuditLog.created_at >= since_date).count()
    
    # By entity type
    by_entity_type = {}
    entity_counts = db.query(
        AuditLog.entity_type,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.created_at >= since_date
    ).group_by(AuditLog.entity_type).all()
    
    for entity_type, count in entity_counts:
        by_entity_type[entity_type] = count
    
    # By action
    by_action = {}
    action_counts = db.query(
        AuditLog.action,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.created_at >= since_date
    ).group_by(AuditLog.action).all()
    
    for action, count in action_counts:
        by_action[action] = count
    
    # Recent activity (last 24 hours)
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    recent_activity_count = db.query(AuditLog).filter(
        AuditLog.created_at >= twenty_four_hours_ago
    ).count()
    
    return AuditLogStats(
        total_logs=total_logs,
        by_entity_type=by_entity_type,
        by_action=by_action,
        recent_activity_count=recent_activity_count
    )


@router.get("/audit-logs/search/recent")
def search_recent_logs(
    minutes: int = Query(60, ge=1, le=1440, description="Minutes to look back"),
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Search recent audit logs.
    
    Query:
    - minutes: How far back to search (1-1440, default 60)
    - entity_type: Optional filter
    - action: Optional filter
    - limit: Max results (1-200)
    
    Returns most recent matching logs.
    """
    since_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    query = db.query(AuditLog).filter(AuditLog.created_at >= since_time)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id),
                "action": log.action,
                "details": log.details or {},
                "actor": log.actor,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "count": len(logs),
        "period_minutes": minutes
    }
