"""
Conflict Detector - Detects conflicts when multiple agents target the same customer
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

from app.models.agent_request import AgentRequest
from app.models.conflict import Conflict
from app.models.customer_contact import CustomerContact

logger = logging.getLogger(__name__)


class ConflictType:
    """Types of conflicts that can be detected"""
    SIMULTANEOUS = "SIMULTANEOUS"  # Multiple requests at the same time (within 60s)
    RAPID_SUCCESSION = "RAPID_SUCCESSION"  # Multiple requests within short window (5min)
    CHANNEL_OVERLAP = "CHANNEL_OVERLAP"  # Same channel, short window (15min)
    INTENT_CONFLICT = "INTENT_CONFLICT"  # Conflicting intents (e.g., marketing + support)


class ConflictSeverity:
    """Severity levels for conflicts"""
    LOW = "LOW"  # Same agent, minor overlap
    MEDIUM = "MEDIUM"  # Different agents, same intent
    HIGH = "HIGH"  # Different agents, different intents
    CRITICAL = "CRITICAL"  # Multiple agents, same channel, simultaneous


class ConflictDetector:
    """
    Detects conflicts when multiple agents target the same customer.
    
    This prevents:
    - Multiple messages sent simultaneously
    - Rapid-fire messaging from different agents
    - Channel saturation
    - Intent conflicts (e.g., marketing during support issue)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_conflicts(
        self,
        customer_id: str,
        current_request: AgentRequest,
        time_window_minutes: int = 15
    ) -> Optional[Conflict]:
        """
        Detect if there are conflicting requests for this customer.
        
        Args:
            customer_id: Customer being targeted
            current_request: The new request being processed
            time_window_minutes: Look-back window for conflicts (default 15min)
        
        Returns:
            Conflict object if conflict detected, None otherwise
        """
        # Get recent requests for this customer (excluding current one)
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        recent_requests = self.db.query(AgentRequest).filter(
            AgentRequest.customer_id == customer_id,
            AgentRequest.created_at >= cutoff_time,
            AgentRequest.id != current_request.id,
            AgentRequest.status.in_(["pending", "processing", "approved"])
        ).all()
        
        if not recent_requests:
            return None
        
        # Analyze conflicts
        conflict_type, severity, details = self._analyze_conflicts(
            current_request,
            recent_requests
        )
        
        if not conflict_type:
            return None
        
        # Create conflict record
        conflict = Conflict(
            customer_id=customer_id,
            request_ids=[str(req.id) for req in recent_requests] + [str(current_request.id)],
            agent_ids=list(set([str(req.agent_id) for req in recent_requests] + [str(current_request.agent_id)])),
            conflict_type=conflict_type,
            severity=severity,
            status="detected",
            conflict_details=details,
            detected_at=datetime.utcnow()
        )
        
        self.db.add(conflict)
        self.db.commit()
        self.db.refresh(conflict)
        
        logger.warning(
            f"Conflict detected: type={conflict_type}, severity={severity}, "
            f"customer={customer_id}, requests={len(recent_requests)+1}"
        )
        
        return conflict
    
    def _analyze_conflicts(
        self,
        current: AgentRequest,
        recent: List[AgentRequest]
    ) -> Tuple[Optional[str], Optional[str], Dict]:
        """
        Analyze the nature and severity of conflicts.
        
        Returns:
            (conflict_type, severity, details)
        """
        details = {
            "current_request": {
                "id": str(current.id),
                "agent_id": str(current.agent_id),
                "intent": current.intent,
                "channel": current.channel,
                "priority": current.priority,
                "created_at": current.created_at.isoformat()
            },
            "conflicting_requests": [
                {
                    "id": str(req.id),
                    "agent_id": str(req.agent_id),
                    "intent": req.intent,
                    "channel": req.channel,
                    "priority": req.priority,
                    "created_at": req.created_at.isoformat()
                }
                for req in recent
            ]
        }
        
        # Check for simultaneous requests (within 60s)
        simultaneous = [
            req for req in recent
            if (current.created_at - req.created_at).total_seconds() < 60
        ]
        
        if simultaneous:
            # Multiple agents targeting customer at the same time
            different_agents = len(set([req.agent_id for req in simultaneous] + [current.agent_id])) > 1
            same_channel = any(req.channel == current.channel for req in simultaneous)
            
            if different_agents and same_channel:
                return ConflictType.SIMULTANEOUS, ConflictSeverity.CRITICAL, details
            elif different_agents:
                return ConflictType.SIMULTANEOUS, ConflictSeverity.HIGH, details
            else:
                return ConflictType.SIMULTANEOUS, ConflictSeverity.MEDIUM, details
        
        # Check for rapid succession (within 5min)
        rapid = [
            req for req in recent
            if (current.created_at - req.created_at).total_seconds() < 300
        ]
        
        if rapid:
            different_agents = len(set([req.agent_id for req in rapid] + [current.agent_id])) > 1
            
            if different_agents:
                return ConflictType.RAPID_SUCCESSION, ConflictSeverity.MEDIUM, details
            else:
                return ConflictType.RAPID_SUCCESSION, ConflictSeverity.LOW, details
        
        # Check for channel overlap (within 15min)
        channel_overlap = [
            req for req in recent
            if req.channel == current.channel
        ]
        
        if channel_overlap:
            return ConflictType.CHANNEL_OVERLAP, ConflictSeverity.MEDIUM, details
        
        # Check for intent conflicts
        conflicting_intents = {
            ("MARKETING", "SUPPORT"),
            ("MARKETING", "PAYMENT_RECOVERY"),
            ("SUPPORT", "PAYMENT_RECOVERY"),
        }
        
        for req in recent:
            intent_pair = tuple(sorted([current.intent, req.intent]))
            if intent_pair in conflicting_intents:
                return ConflictType.INTENT_CONFLICT, ConflictSeverity.HIGH, details
        
        # Default: some conflict exists but not categorized
        return ConflictType.RAPID_SUCCESSION, ConflictSeverity.LOW, details
    
    def get_recent_conflicts(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Conflict]:
        """
        Get recent conflicts, optionally filtered.
        
        Args:
            customer_id: Filter by customer
            status: Filter by status
            limit: Max results
        
        Returns:
            List of conflicts
        """
        query = self.db.query(Conflict)
        
        if customer_id:
            query = query.filter(Conflict.customer_id == customer_id)
        
        if status:
            query = query.filter(Conflict.status == status)
        
        return query.order_by(Conflict.detected_at.desc()).limit(limit).all()
    
    def mark_resolved(
        self,
        conflict_id: str,
        resolution_strategy: str,
        merged_request_id: Optional[str] = None,
        resolution_metadata: Optional[Dict] = None
    ):
        """
        Mark a conflict as resolved.
        
        Args:
            conflict_id: Conflict ID
            resolution_strategy: How it was resolved
            merged_request_id: If merged, the resulting request ID
            resolution_metadata: Additional details
        """
        conflict = self.db.query(Conflict).filter(Conflict.id == conflict_id).first()
        
        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        conflict.status = "resolved"
        conflict.resolution_strategy = resolution_strategy
        conflict.merged_request_id = merged_request_id
        conflict.resolution_metadata = resolution_metadata or {}
        conflict.resolved_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(
            f"Conflict resolved: id={conflict_id}, strategy={resolution_strategy}, "
            f"merged_request={merged_request_id}"
        )
