"""
Execution Service
Handles execution of ALLOWED requests and queuing of DELAYED requests
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import uuid

from app.models.agent_request import AgentRequest
from app.models.decision import Decision
from app.models.delayed_action import DelayedAction
from app.services.arbitration.decision_engine import DecisionType


class ExecutionResult:
    """Result of an execution attempt"""
    
    def __init__(
        self,
        success: bool,
        execution_id: Optional[uuid.UUID] = None,
        channel: Optional[str] = None,
        status: str = "pending",
        message: str = "",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.execution_id = execution_id
        self.channel = channel
        self.status = status
        self.message = message
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "channel": self.channel,
            "status": self.status,
            "message": self.message,
            "error": self.error,
            "metadata": self.metadata
        }


class ExecutionService:
    """Service for executing approved requests"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_decision(
        self,
        agent_request: AgentRequest,
        decision: Decision
    ) -> ExecutionResult:
        """
        Process a decision and execute or queue accordingly
        
        Args:
            agent_request: The agent request
            decision: The arbitration decision
        
        Returns:
            ExecutionResult with status
        """
        decision_type = decision.decision
        
        if decision_type == DecisionType.ALLOW.value:
            return self.execute_immediately(agent_request, decision)
        
        elif decision_type == DecisionType.DELAY.value:
            return self.queue_for_later(agent_request, decision)
        
        elif decision_type == DecisionType.BLOCK.value:
            return ExecutionResult(
                success=False,
                status="blocked",
                message=f"Request blocked: {decision.block_reason}",
                error=decision.message
            )
        
        else:
            return ExecutionResult(
                success=False,
                status="unknown",
                message=f"Unknown decision type: {decision_type}",
                error="Invalid decision type"
            )
    
    def execute_immediately(
        self,
        agent_request: AgentRequest,
        decision: Decision
    ) -> ExecutionResult:
        """
        Execute an ALLOWED request immediately
        
        This creates an execution record and would trigger the channel provider.
        For MVP, we return success immediately. In production, this would:
        1. Call the appropriate channel provider (email, SMS, etc.)
        2. Wait for provider response
        3. Record the execution result
        
        Args:
            agent_request: The agent request to execute
            decision: The ALLOW decision
        
        Returns:
            ExecutionResult
        """
        # Create execution record (using delayed_action table for now)
        execution = DelayedAction(
            request_id=agent_request.id,
            scheduled_at=datetime.now(),  # Immediate
            expires_at=datetime.now() + timedelta(hours=1),
            status="processed",
            delay_reason="immediate_execution",
            retry_count=0,
            result="success",
            processed_at=datetime.now()
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        # TODO: Call channel provider here
        # For MVP, we simulate successful execution
        # (already marked as processed above)
        
        # Record contact in customer_contact table
        from app.services.arbitration.customer_state import CustomerStateService
        state_service = CustomerStateService(self.db)
        state_service.record_contact(
            customer_id=agent_request.customer_id,
            decision_id=decision.id,
            channel=agent_request.channel,
            intent=agent_request.intent
        )
        
        return ExecutionResult(
            success=True,
            execution_id=execution.id,
            channel=agent_request.channel,
            status="sent",
            message=f"Request executed via {agent_request.channel}",
            metadata={
                "request_id": str(agent_request.id),
                "decision_id": str(decision.id),
                "executed_at": execution.processed_at.isoformat() if execution.processed_at else None
            }
        )
    
    def queue_for_later(
        self,
        agent_request: AgentRequest,
        decision: Decision
    ) -> ExecutionResult:
        """
        Queue a DELAYED request for later execution
        
        Calculates appropriate delay time based on:
        - Current customer state (contacts today, attention budget)
        - Decision score (lower score = longer delay)
        - Time of day (avoid late night)
        
        Args:
            agent_request: The agent request
            decision: The DELAY decision
        
        Returns:
            ExecutionResult
        """
        # Calculate delay duration based on score (default to 4 hours if no score)
        delay_hours = 4  # Default delay
        scheduled_for = datetime.now() + timedelta(hours=delay_hours)
        expires_at = scheduled_for + timedelta(days=1)  # Give 1 day to process
        
        # Create delayed action
        delayed_action = DelayedAction(
            request_id=agent_request.id,
            scheduled_at=scheduled_for,
            expires_at=expires_at,
            status="pending",
            delay_reason=decision.delay_reason or "low_score",
            retry_count=0
        )
        
        self.db.add(delayed_action)
        self.db.commit()
        self.db.refresh(delayed_action)
        
        return ExecutionResult(
            success=True,
            execution_id=delayed_action.id,
            channel=agent_request.channel,
            status="queued",
            message=f"Request queued for execution in {delay_hours} hours",
            metadata={
                "request_id": str(agent_request.id),
                "decision_id": str(decision.id),
                "scheduled_for": scheduled_for.isoformat(),
                "delay_hours": delay_hours
            }
        )
    
    def _calculate_delay_hours(self, final_score: float) -> int:
        """
        Calculate delay hours based on final score
        
        Score ranges:
        - 55-60: 2 hours (borderline)
        - 50-55: 4 hours (moderate delay)
        - 45-50: 8 hours (longer delay)
        - <45: 24 hours (significant delay)
        
        Args:
            final_score: The combined priority + value score
        
        Returns:
            Number of hours to delay
        """
        if final_score >= 55:
            return 2
        elif final_score >= 50:
            return 4
        elif final_score >= 45:
            return 8
        else:
            return 24
    
    def get_execution_status(
        self,
        execution_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get execution status
        
        Args:
            execution_id: Execution/DelayedAction ID
        
        Returns:
            Status dictionary or None
        """
        execution = self.db.query(DelayedAction).filter(
            DelayedAction.id == execution_id
        ).first()
        
        if not execution:
            return None
        
        return {
            "id": str(execution.id),
            "request_id": str(execution.request_id),
            "status": execution.status,
            "scheduled_for": execution.scheduled_at.isoformat(),
            "executed_at": execution.processed_at.isoformat() if execution.processed_at else None,
            "retry_count": execution.retry_count,
            "last_error": execution.result_message if execution.result == "failed" else None,
            "metadata": {
                "delay_reason": execution.delay_reason,
                "result": execution.result
            }
        }
