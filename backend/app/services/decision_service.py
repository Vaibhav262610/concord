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
        # Get the agent request to extract customer_id
        from app.models.agent_request import AgentRequest
        agent_request = self.db.query(AgentRequest).filter(AgentRequest.id == request_id).first()
        if not agent_request:
            raise ValueError(f"Agent request {request_id} not found")
        
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
            customer_id=agent_request.customer_id,  # Get from agent_request
            decision=decision_type.value,
            # Removed: final_score, priority_score, value_score (not in model)
            reason_code=decision_details.get("reason_code", "UNKNOWN"),
            reason=message if message else "Decision processed",
            # block_reason, delay_reason removed (not in this model)
            policy_ids=decision_details.get("policy_ids", []),
            conflicting_requests=decision_details.get("conflicting_requests", []),
            merged_with=decision_details.get("merged_with"),
            merged_message=decision_details.get("merged_message"),
            scheduled_at=decision_details.get("scheduled_at"),
            delay_reason=delay_reason,
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
            # Note: Decision model doesn't have these fields
            reason=decision.reason,
            reason_code=decision.reason_code,
            delay_reason=decision.delay_reason,
            created_at=decision.created_at
        )
    
    def to_detail(self, decision: Decision) -> DecisionDetail:
        """Convert Decision model to detailed schema"""
        
        return DecisionDetail(
            id=decision.id,
            request_id=decision.request_id,
            decision=decision.decision,
            # Note: Decision model doesn't have score fields
            reason=decision.reason,
            reason_code=decision.reason_code,
            delay_reason=decision.delay_reason,
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
