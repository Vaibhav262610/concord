"""
Gateway service for agent action request processing
Handles validation, idempotency, and request persistence
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional, Tuple
import uuid

from app.models.agent import Agent
from app.models.agent_request import AgentRequest
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.models.decision import Decision
from app.schemas.agent_request import AgentActionRequest
from app.services.auth import check_agent_permission
from app.services.arbitration import DecisionEngine, DecisionType
from app.services.decision_service import DecisionService
from app.services.execution_service import ExecutionService, ExecutionResult
from app.exceptions import ValidationError as ConcordValidationError


class ValidationError(Exception):
    """Custom exception for validation errors (keeping for backward compatibility)"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class GatewayService:
    """Service for processing agent action requests through the gateway"""
    
    def __init__(self, db: Session):
        self.db = db
        self.decision_engine = DecisionEngine(db)
        self.decision_service = DecisionService(db)
        self.execution_service = ExecutionService(db)
    
    def check_idempotency(self, request_id: str) -> Optional[AgentRequest]:
        """
        Check if request_id already exists (idempotency check)
        
        Args:
            request_id: Unique request identifier
        
        Returns:
            Existing AgentRequest if found, None otherwise
        """
        existing_request = self.db.query(AgentRequest).filter(
            AgentRequest.request_id == request_id
        ).first()
        
        return existing_request
    
    def validate_agent_permissions(
        self,
        agent: Agent,
        request: AgentActionRequest
    ) -> None:
        """
        Validate agent has required permissions for this action
        
        Args:
            agent: Authenticated agent
            request: Action request
        
        Raises:
            ValidationError: If agent lacks required permission
        """
        # Check messaging permission
        if not check_agent_permission(agent, "messaging"):
            raise ValidationError(
                "PERMISSION_DENIED",
                "Agent does not have 'messaging' permission"
            )
        
        # Check discount permission if offer present
        if request.offer:
            if not check_agent_permission(agent, "discounts"):
                raise ValidationError(
                    "PERMISSION_DENIED",
                    "Agent does not have 'discounts' permission"
                )
            
            # Check high value discount permission
            if request.offer.value > 15:  # More than 15% or high amount
                if not check_agent_permission(agent, "high_value_discounts"):
                    raise ValidationError(
                        "PERMISSION_DENIED",
                        "Agent does not have 'high_value_discounts' permission for offers > 15%"
                    )
    
    def validate_request_expiry(self, request: AgentActionRequest) -> None:
        """
        Validate request expiry time
        
        Args:
            request: Action request
        
        Raises:
            ValidationError: If request already expired
        """
        if request.expires_at and request.expires_at < datetime.utcnow():
            raise ValidationError(
                "REQUEST_EXPIRED",
                f"Request expired at {request.expires_at.isoformat()}"
            )
    
    def validate_offer(self, request: AgentActionRequest) -> None:
        """
        Validate offer details
        
        Args:
            request: Action request
        
        Raises:
            ValidationError: If offer is invalid
        """
        if not request.offer:
            return
        
        offer = request.offer
        
        # Validate discount value
        if offer.unit == "PERCENT":
            if offer.value > 100:
                raise ValidationError(
                    "INVALID_OFFER",
                    "Discount percentage cannot exceed 100%"
                )
            if offer.value < 0:
                raise ValidationError(
                    "INVALID_OFFER",
                    "Discount percentage cannot be negative"
                )
        
        # Validate amounts
        if offer.unit == "AMOUNT":
            if offer.value < 0:
                raise ValidationError(
                    "INVALID_OFFER",
                    "Discount amount cannot be negative"
                )
        
        # Validate max_amount if present
        if offer.max_amount and offer.max_amount < 0:
            raise ValidationError(
                "INVALID_OFFER",
                "Maximum discount amount cannot be negative"
            )
        
        # Validate min_order_value if present
        if offer.min_order_value and offer.min_order_value < 0:
            raise ValidationError(
                "INVALID_OFFER",
                "Minimum order value cannot be negative"
            )
    
    def resolve_customer(
        self,
        agent: Agent,
        customer_id: str
    ) -> Customer:
        """
        Resolve customer identifier to CONCORD customer
        
        Args:
            agent: Authenticated agent
            customer_id: Customer identifier from agent
        
        Returns:
            Customer instance
        
        Raises:
            ValidationError: If customer not found
        """
        # Try to find customer by external_id
        customer = self.db.query(Customer).filter(
            Customer.merchant_id == agent.merchant_id,
            Customer.external_id == customer_id
        ).first()
        
        if not customer:
            # For now, create customer if not exists (in production, this might be different)
            # In real scenario, customer should be created through a separate endpoint
            raise ValidationError(
                "CUSTOMER_NOT_FOUND",
                f"Customer '{customer_id}' not found. Create customer first."
            )
        
        return customer
    
    def create_agent_request(
        self,
        agent: Agent,
        customer: Customer,
        request: AgentActionRequest
    ) -> AgentRequest:
        """
        Create and persist agent request to database
        
        Args:
            agent: Authenticated agent
            customer: Resolved customer
            request: Validated action request
        
        Returns:
            Created AgentRequest instance
        
        Raises:
            IntegrityError: If database constraint violated
        """
        agent_request = AgentRequest(
            request_id=request.request_id,
            merchant_id=agent.merchant_id,
            agent_id=agent.id,
            customer_id=customer.id,
            action_type=request.action.value,
            intent=request.intent.value,
            channel=request.channel.value,
            priority=request.priority,
            estimated_value=request.estimated_value,
            urgency=request.urgency.value if request.urgency else None,
            offer=request.offer.model_dump() if request.offer else None,
            message=request.message,
            expires_at=request.expires_at,
            custom_metadata=request.custom_metadata or {},
            status="pending"
        )
        
        try:
            self.db.add(agent_request)
            self.db.commit()
            self.db.refresh(agent_request)
        except IntegrityError as e:
            self.db.rollback()
            # This shouldn't happen if idempotency check passed, but handle it
            raise ValidationError(
                "DUPLICATE_REQUEST",
                f"Request ID '{request.request_id}' already exists"
            )
        
        return agent_request
    
    def log_request_received(
        self,
        agent_request: AgentRequest,
        agent: Agent
    ) -> None:
        """
        Create audit log for received request
        
        Args:
            agent_request: Created agent request
            agent: Agent who made the request
        """
        audit_log = AuditLog(
            entity_type="agent_request",
            entity_id=agent_request.id,
            action="REQUEST_RECEIVED",
            details={
                "request_id": agent_request.request_id,
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "customer_id": str(agent_request.customer_id),
                "intent": agent_request.intent,
                "channel": agent_request.channel,
                "priority": agent_request.priority,
                "estimated_value": agent_request.estimated_value,
                "has_offer": agent_request.offer is not None
            },
            actor=f"agent:{agent.id}",
            customer_id=agent_request.customer_id
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    def run_arbitration(
        self,
        agent_request: AgentRequest
    ) -> Tuple[DecisionType, Decision, ExecutionResult]:
        """
        Run arbitration engine on agent request and execute if approved
        
        This is where CONCORD's core decision-making happens:
        - Checks consent, frequency, policy compliance
        - Calculates priority and business value scores
        - Makes ALLOW/BLOCK/DELAY decision
        - Executes or queues based on decision
        
        Args:
            agent_request: Agent request to arbitrate
        
        Returns:
            Tuple of (DecisionType, Decision record, ExecutionResult)
        """
        # Run decision engine
        decision_type, decision_details = self.decision_engine.make_decision(agent_request)
        
        # Persist decision to database
        decision = self.decision_service.create_decision(
            request_id=agent_request.id,
            decision_type=decision_type,
            decision_details=decision_details
        )
        
        # Update agent request status based on decision
        if decision_type == DecisionType.ALLOW:
            agent_request.status = "approved"
        elif decision_type == DecisionType.BLOCK:
            agent_request.status = "blocked"
        elif decision_type == DecisionType.DELAY:
            agent_request.status = "delayed"
        
        self.db.commit()
        self.db.refresh(agent_request)
        
        # Log decision to audit trail
        self._log_decision(agent_request, decision)
        
        # Execute or queue based on decision
        execution_result = self.execution_service.process_decision(agent_request, decision)
        
        # Log execution
        self._log_execution(agent_request, decision, execution_result)
        
        return decision_type, decision, execution_result
    
    def _log_decision(
        self,
        agent_request: AgentRequest,
        decision: Decision
    ) -> None:
        """
        Create audit log for arbitration decision
        
        Args:
            agent_request: Agent request
            decision: Decision record
        """
        audit_log = AuditLog(
            entity_type="decision",
            entity_id=decision.id,
            action=f"DECISION_{decision.decision}",
            details={
                "request_id": str(agent_request.id),
                "decision": decision.decision,
                "final_score": decision.final_score,
                "priority_score": decision.priority_score,
                "value_score": decision.value_score,
                "block_reason": decision.block_reason,
                "delay_reason": decision.delay_reason,
                "message": decision.message
            },
            actor="system:arbitration_engine",
            customer_id=agent_request.customer_id
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    def _log_execution(
        self,
        agent_request: AgentRequest,
        decision: Decision,
        execution_result: ExecutionResult
    ) -> None:
        """
        Create audit log for execution
        
        Args:
            agent_request: Agent request
            decision: Decision record
            execution_result: Execution result
        """
        audit_log = AuditLog(
            entity_type="execution",
            entity_id=execution_result.execution_id or agent_request.id,
            action=f"EXECUTION_{execution_result.status.upper()}",
            details={
                "request_id": str(agent_request.id),
                "decision_id": str(decision.id),
                "channel": execution_result.channel,
                "status": execution_result.status,
                "success": execution_result.success,
                "message": execution_result.message,
                "error": execution_result.error,
                "metadata": execution_result.metadata
            },
            actor="system:execution_engine",
            customer_id=agent_request.customer_id
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    def process_action_request(
        self,
        agent: Agent,
        request: AgentActionRequest,
        run_arbitration: bool = True
    ) -> Tuple[AgentRequest, bool, Optional[Decision], Optional[ExecutionResult]]:
        """
        Process an agent action request through the gateway
        
        This is the main entry point that orchestrates:
        1. Idempotency check
        2. Permission validation
        3. Request validation
        4. Customer resolution
        5. Request persistence
        6. Audit logging
        7. Arbitration (if enabled)
        8. Execution (if approved/delayed)
        
        Args:
            agent: Authenticated agent
            request: Action request from agent
            run_arbitration: Whether to run arbitration engine (default: True)
        
        Returns:
            Tuple of (AgentRequest, is_duplicate, Decision, ExecutionResult)
            - AgentRequest: Created or existing request
            - is_duplicate: True if this was a duplicate request (idempotent)
            - Decision: Arbitration decision (None if duplicate or arbitration disabled)
            - ExecutionResult: Execution result (None if not executed)
        
        Raises:
            ValidationError: If validation fails
        """
        # Step 1: Check idempotency
        existing_request = self.check_idempotency(request.request_id)
        if existing_request:
            # Idempotent - return existing request
            # Get existing decision if available
            existing_decision = self.decision_service.get_decision_by_request(existing_request.id)
            # Get existing execution if available
            existing_execution = self.execution_service.get_execution_status(existing_request.id)
            execution_result = ExecutionResult(
                success=True,
                status=existing_execution.get("status") if existing_execution else "unknown",
                message="Duplicate request - returning cached result"
            ) if existing_execution else None
            return existing_request, True, existing_decision, execution_result
        
        # Step 2: Validate agent permissions
        self.validate_agent_permissions(agent, request)
        
        # Step 3: Validate request
        self.validate_request_expiry(request)
        self.validate_offer(request)
        
        # Step 4: Resolve customer
        customer = self.resolve_customer(agent, request.customer_id)
        
        # Step 5: Create agent request
        agent_request = self.create_agent_request(agent, customer, request)
        
        # Step 6: Log to audit trail
        self.log_request_received(agent_request, agent)
        
        # Step 7 & 8: Run arbitration and execution if enabled
        decision = None
        execution_result = None
        if run_arbitration:
            decision_type, decision, execution_result = self.run_arbitration(agent_request)
        
        return agent_request, False, decision, execution_result
    
    def get_agent_requests(
        self,
        merchant_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[list[AgentRequest], int]:
        """
        Get list of agent requests with filters
        
        Args:
            merchant_id: Filter by merchant
            customer_id: Optional filter by customer
            agent_id: Optional filter by agent
            status: Optional filter by status
            limit: Number of results per page
            offset: Pagination offset
        
        Returns:
            Tuple of (list of requests, total count)
        """
        query = self.db.query(AgentRequest).filter(
            AgentRequest.merchant_id == merchant_id
        )
        
        if customer_id:
            query = query.filter(AgentRequest.customer_id == customer_id)
        
        if agent_id:
            query = query.filter(AgentRequest.agent_id == agent_id)
        
        if status:
            query = query.filter(AgentRequest.status == status)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        requests = query.order_by(
            AgentRequest.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return requests, total
    
    def get_agent_request_by_id(
        self,
        request_id: uuid.UUID,
        merchant_id: uuid.UUID
    ) -> Optional[AgentRequest]:
        """
        Get specific agent request by ID
        
        Args:
            request_id: Request UUID
            merchant_id: Merchant ID (for authorization)
        
        Returns:
            AgentRequest if found and authorized, None otherwise
        """
        return self.db.query(AgentRequest).filter(
            AgentRequest.id == request_id,
            AgentRequest.merchant_id == merchant_id
        ).first()
