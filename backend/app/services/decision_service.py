"""
Decision Service
Handles decision persistence and retrieval
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from app.models.decision import Decision
from app.models.agent_request import AgentRequest
from app.services.arbitration.decision_engine import DecisionType
from app.schemas.decision import DecisionResponse, DecisionDetail, DecisionList


class DecisionService:
    """Service for managing arbitration decisions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_decision(
        self,
        request_id: UUID,
        decision_type: DecisionType,
        decision_details: Dict[str, Any]
    ) -> Decision:
        """
        Persist arbitration decision to database
        
        Args:
            request_id: Agent request UUID
            decision_type: Decision type (ALLOW, BLOCK, DELAY)
            decision_details: Full decision details dictionary
        
        Returns:
            Created Decision record
        """
        # Extract key fields
        final_score = decision_details.get("final_score")
        
        priority_check = decision_details.get("checks", {}).get("priority", {})
        priority_score = priority_check.get("score")
        
        value_check = decision_details.get("checks", {}).get("business_value", {})
        value_score = value_check.get("score")
        
        block_reason = decision_details.get("block_reason")
        delay_reason = decision_details.get("delay_reason")
        message = decision_details.get("message", "")
        warnings = decision_details.get("warnings")
        
        decision = Decision(
            request_id=request_id,
            decision=decision_type.value,
            final_score=final_score,
            priority_score=priority_score,
            value_score=value_score,
            block_reason=block_reason,
            delay_reason=delay_reason,
            message=message,
            warnings=warnings,
            details=decision_details  # Store full details as JSON
        )
        
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        
        return decision
    
    def get_decision(self, decision_id: UUID) -> Optional[Decision]:
        """Get decision by ID"""
        return self.db.query(Decision).filter(Decision.id == decision_id).first()
    
    def get_decision_by_request(self, request_id: UUID) -> Optional[Decision]:
        """Get decision for a specific request"""
        return self.db.query(Decision).filter(
            Decision.request_id == request_id
        ).order_by(Decision.created_at.desc()).first()
    
    def get_decisions(
        self,
        customer_id: Optional[UUID] = None,
        decision_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Decision], int]:
        """
        Get paginated list of decisions
        
        Args:
            customer_id: Filter by customer
            decision_type: Filter by decision (ALLOW, BLOCK, DELAY)
            page: Page number (1-indexed)
            page_size: Items per page
        
        Returns:
            Tuple of (decisions_list, total_count)
        """
        query = self.db.query(Decision).join(AgentRequest)
        
        if customer_id:
            query = query.filter(AgentRequest.customer_id == customer_id)
        
        if decision_type:
            query = query.filter(Decision.decision == decision_type)
        
        total = query.count()
        
        decisions = query.order_by(Decision.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return decisions, total
    
    def to_response(self, decision: Decision) -> DecisionResponse:
        """Convert Decision model to response schema"""
        return DecisionResponse(
            id=decision.id,
            request_id=decision.request_id,
            decision=decision.decision,
            final_score=decision.final_score,
            priority_score=decision.priority_score,
            value_score=decision.value_score,
            block_reason=decision.block_reason,
            delay_reason=decision.delay_reason,
            message=decision.message,
            warnings=decision.warnings,
            created_at=decision.created_at
        )
    
    def to_detail(self, decision: Decision) -> DecisionDetail:
        """Convert Decision model to detailed schema"""
        details = decision.details or {}
        
        return DecisionDetail(
            id=decision.id,
            request_id=decision.request_id,
            decision=decision.decision,
            final_score=decision.final_score,
            message=decision.message,
            block_reason=decision.block_reason,
            delay_reason=decision.delay_reason,
            warnings=decision.warnings,
            customer_state=details.get("customer_state", {}),
            policy_rules=details.get("policy_rules", {}),
            checks=details.get("checks", {}),
            score_weights=details.get("score_weights"),
            created_at=decision.created_at
        )
    
    def to_list(
        self,
        decisions: List[Decision],
        total: int,
        page: int,
        page_size: int
    ) -> DecisionList:
        """Convert list of decisions to list schema"""
        return DecisionList(
            decisions=[self.to_response(d) for d in decisions],
            total=total,
            page=page,
            page_size=page_size
        )
