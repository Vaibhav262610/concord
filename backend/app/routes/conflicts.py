"""
Conflict Resolution API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models.conflict import Conflict
from app.services.arbitration.conflict_detector import ConflictDetector
from app.services.arbitration.merge_engine import MergeEngine
from app.schemas.conflict import (
    ConflictResponse,
    ConflictListResponse,
    MergeRecommendationResponse,
    MergeRequest,
    MergeResult
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/conflicts", response_model=ConflictListResponse)
def list_conflicts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    customer_id: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(detected|analyzing|resolved|merged|suppressed)$"),
    severity: Optional[str] = Query(None, regex="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    db: Session = Depends(get_db)
):
    """
    List detected conflicts.
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Max records to return
    - customer_id: Filter by customer
    - status: Filter by status
    - severity: Filter by severity
    """
    query = db.query(Conflict)
    
    if customer_id:
        query = query.filter(Conflict.customer_id == customer_id)
    
    if status:
        query = query.filter(Conflict.status == status)
    
    if severity:
        query = query.filter(Conflict.severity == severity)
    
    total = query.count()
    conflicts = query.order_by(Conflict.detected_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "conflicts": conflicts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/conflicts/{conflict_id}", response_model=ConflictResponse)
def get_conflict(
    conflict_id: str,
    db: Session = Depends(get_db)
):
    """Get conflict details by ID."""
    conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    return conflict


@router.get("/conflicts/{conflict_id}/recommendation", response_model=MergeRecommendationResponse)
def get_merge_recommendation(
    conflict_id: str,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered merge recommendation for a conflict.
    
    Analyzes the conflicting requests and recommends the best merge strategy.
    """
    conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    if conflict.status != "detected":
        raise HTTPException(
            status_code=400,
            detail=f"Conflict already {conflict.status}. Cannot get recommendation."
        )
    
    merge_engine = MergeEngine(db)
    recommendation = merge_engine.get_merge_recommendation(conflict)
    
    return recommendation


@router.post("/conflicts/{conflict_id}/merge", response_model=MergeResult)
def merge_conflict(
    conflict_id: str,
    merge_request: MergeRequest,
    db: Session = Depends(get_db)
):
    """
    Merge conflicting requests using specified strategy.
    
    Body:
    - strategy: Merge strategy (optional, auto-select if not provided)
    """
    conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    if conflict.status not in ["detected", "analyzing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Conflict already {conflict.status}. Cannot merge."
        )
    
    try:
        merge_engine = MergeEngine(db)
        winner = merge_engine.merge_requests(
            conflict,
            strategy=merge_request.strategy
        )
        
        return {
            "success": True,
            "conflict_id": str(conflict.id),
            "winning_request_id": str(winner.id),
            "strategy_used": conflict.resolution_strategy,
            "suppressed_count": len(conflict.request_ids) - 1,
            "message": f"Successfully merged {len(conflict.request_ids)} requests"
        }
    
    except Exception as e:
        logger.error(f"Failed to merge conflict {conflict_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark conflict as manually resolved.
    
    Use this when conflict was resolved through external means.
    """
    conflict = db.query(Conflict).filter(Conflict.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    if conflict.status == "resolved":
        return {"message": "Conflict already resolved"}
    
    detector = ConflictDetector(db)
    detector.mark_resolved(
        conflict_id,
        resolution_strategy="MANUAL",
        resolution_metadata={"resolved_by": "manual_intervention"}
    )
    
    return {
        "success": True,
        "conflict_id": str(conflict_id),
        "message": "Conflict marked as resolved"
    }


@router.get("/conflicts/stats/summary")
def get_conflict_stats(
    db: Session = Depends(get_db)
):
    """
    Get conflict statistics.
    
    Returns aggregated metrics about conflicts.
    """
    from sqlalchemy import func
    
    # Total conflicts
    total = db.query(func.count(Conflict.id)).scalar()
    
    # By status
    by_status = db.query(
        Conflict.status,
        func.count(Conflict.id)
    ).group_by(Conflict.status).all()
    
    # By severity
    by_severity = db.query(
        Conflict.severity,
        func.count(Conflict.id)
    ).group_by(Conflict.severity).all()
    
    # By type
    by_type = db.query(
        Conflict.conflict_type,
        func.count(Conflict.id)
    ).group_by(Conflict.conflict_type).all()
    
    # Resolution strategies
    by_strategy = db.query(
        Conflict.resolution_strategy,
        func.count(Conflict.id)
    ).filter(Conflict.resolution_strategy.isnot(None)).group_by(
        Conflict.resolution_strategy
    ).all()
    
    return {
        "total_conflicts": total,
        "by_status": {status: count for status, count in by_status},
        "by_severity": {severity: count for severity, count in by_severity},
        "by_type": {ctype: count for ctype, count in by_type},
        "by_resolution_strategy": {strategy: count for strategy, count in by_strategy}
    }
