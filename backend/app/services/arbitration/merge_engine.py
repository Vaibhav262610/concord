"""
Merge Engine - Intelligently merges conflicting requests
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.models.agent_request import AgentRequest
from app.models.conflict import Conflict

logger = logging.getLogger(__name__)


class MergeStrategy:
    """Strategies for merging conflicting requests"""
    PRIORITIZE_HIGHEST = "PRIORITIZE_HIGHEST"  # Keep highest priority
    PRIORITIZE_VALUE = "PRIORITIZE_VALUE"  # Keep highest estimated value
    PRIORITIZE_URGENT = "PRIORITIZE_URGENT"  # Keep most urgent
    COMBINE_MESSAGES = "COMBINE_MESSAGES"  # Merge message content
    SUPPRESS_LOWER = "SUPPRESS_LOWER"  # Suppress all lower priority
    DELAY_CONFLICTING = "DELAY_CONFLICTING"  # Delay conflicting requests
    LLM_DECIDE = "LLM_DECIDE"  # Use LLM to decide (future)


class MergeEngine:
    """
    Intelligently merges conflicting requests to prevent customer fatigue.
    
    Strategies:
    1. Priority-based: Keep highest priority, suppress others
    2. Value-based: Keep highest business value
    3. Urgency-based: Keep most time-sensitive
    4. Content merge: Combine compatible messages
    5. Delay: Delay lower-priority conflicts
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def merge_requests(
        self,
        conflict: Conflict,
        strategy: Optional[str] = None
    ) -> AgentRequest:
        """
        Merge conflicting requests using specified strategy.
        
        Args:
            conflict: The detected conflict
            strategy: Merge strategy to use (auto-select if None)
        
        Returns:
            The merged/winning request
        """
        # Load all conflicting requests
        request_ids = conflict.request_ids
        requests = self.db.query(AgentRequest).filter(
            AgentRequest.id.in_(request_ids)
        ).all()
        
        if not requests:
            raise ValueError("No requests found for conflict")
        
        if len(requests) == 1:
            return requests[0]
        
        # Auto-select strategy if not provided
        if not strategy:
            strategy = self._select_strategy(conflict, requests)
        
        logger.info(
            f"Merging {len(requests)} requests using strategy: {strategy}"
        )
        
        # Apply merge strategy
        if strategy == MergeStrategy.PRIORITIZE_HIGHEST:
            winner = self._merge_by_priority(requests)
        elif strategy == MergeStrategy.PRIORITIZE_VALUE:
            winner = self._merge_by_value(requests)
        elif strategy == MergeStrategy.PRIORITIZE_URGENT:
            winner = self._merge_by_urgency(requests)
        elif strategy == MergeStrategy.COMBINE_MESSAGES:
            winner = self._merge_by_combining(requests)
        elif strategy == MergeStrategy.SUPPRESS_LOWER:
            winner = self._merge_by_suppression(requests)
        elif strategy == MergeStrategy.DELAY_CONFLICTING:
            winner = self._merge_by_delaying(requests)
        else:
            # Default to priority-based
            winner = self._merge_by_priority(requests)
        
        # Mark conflict as resolved
        conflict.status = "merged"
        conflict.resolution_strategy = strategy
        conflict.merged_request_id = winner.id
        conflict.resolved_at = datetime.utcnow()
        conflict.resolution_metadata = {
            "winning_request_id": str(winner.id),
            "suppressed_request_ids": [str(r.id) for r in requests if r.id != winner.id],
            "strategy_applied": strategy
        }
        
        self.db.commit()
        
        logger.info(
            f"Conflict merged: winner={winner.id}, strategy={strategy}, "
            f"suppressed={len(requests)-1}"
        )
        
        return winner
    
    def _select_strategy(
        self,
        conflict: Conflict,
        requests: List[AgentRequest]
    ) -> str:
        """
        Auto-select the best merge strategy based on conflict type and requests.
        """
        # CRITICAL severity: Suppress lower priority
        if conflict.severity == "CRITICAL":
            return MergeStrategy.SUPPRESS_LOWER
        
        # SIMULTANEOUS conflicts: Prioritize highest
        if conflict.conflict_type == "SIMULTANEOUS":
            return MergeStrategy.PRIORITIZE_HIGHEST
        
        # Check if requests have significantly different priorities
        priorities = [r.priority or 50 for r in requests]
        if max(priorities) - min(priorities) > 30:
            return MergeStrategy.PRIORITIZE_HIGHEST
        
        # Check if requests have significantly different values
        values = [r.estimated_value or 0 for r in requests]
        if max(values) > 0 and max(values) / (min([v for v in values if v > 0]) or 1) > 5:
            return MergeStrategy.PRIORITIZE_VALUE
        
        # Check for urgency differences
        urgency_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        urgencies = [urgency_map.get(r.urgency, 1) for r in requests]
        if max(urgencies) - min(urgencies) >= 2:
            return MergeStrategy.PRIORITIZE_URGENT
        
        # Check if all same intent and channel (can combine)
        intents = set(r.intent for r in requests)
        channels = set(r.channel for r in requests)
        if len(intents) == 1 and len(channels) == 1:
            return MergeStrategy.COMBINE_MESSAGES
        
        # Default: prioritize by value
        return MergeStrategy.PRIORITIZE_VALUE
    
    def _merge_by_priority(self, requests: List[AgentRequest]) -> AgentRequest:
        """Select request with highest priority."""
        winner = max(requests, key=lambda r: r.priority or 0)
        self._suppress_losers(requests, winner)
        return winner
    
    def _merge_by_value(self, requests: List[AgentRequest]) -> AgentRequest:
        """Select request with highest estimated value."""
        winner = max(requests, key=lambda r: r.estimated_value or 0)
        self._suppress_losers(requests, winner)
        return winner
    
    def _merge_by_urgency(self, requests: List[AgentRequest]) -> AgentRequest:
        """Select request with highest urgency."""
        urgency_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, None: 0}
        winner = max(requests, key=lambda r: urgency_map.get(r.urgency, 0))
        self._suppress_losers(requests, winner)
        return winner
    
    def _merge_by_combining(self, requests: List[AgentRequest]) -> AgentRequest:
        """
        Combine compatible messages into one.
        Uses highest priority request as base, appends other messages.
        """
        winner = max(requests, key=lambda r: r.priority or 0)
        
        # Combine messages (simple concatenation for MVP)
        messages = [r.message for r in requests if r.message]
        if messages:
            combined_message = " | ".join(messages)
            winner.message = combined_message[:500]  # Limit length
        
        # Combine offers (take best discount)
        offers = [r.offer for r in requests if r.offer]
        if offers:
            best_offer = max(offers, key=lambda o: o.get("discount_value", 0))
            winner.offer = best_offer
        
        self._suppress_losers(requests, winner)
        return winner
    
    def _merge_by_suppression(self, requests: List[AgentRequest]) -> AgentRequest:
        """Suppress all lower priority requests."""
        winner = max(requests, key=lambda r: r.priority or 0)
        
        for req in requests:
            if req.id != winner.id:
                req.status = "suppressed"
                req.result = "SUPPRESSED"
                req.result_message = f"Suppressed due to conflict (winner: {winner.id})"
        
        self.db.commit()
        return winner
    
    def _merge_by_delaying(self, requests: List[AgentRequest]) -> AgentRequest:
        """
        Keep highest priority, delay others.
        This allows eventual delivery but prevents simultaneous contact.
        """
        winner = max(requests, key=lambda r: r.priority or 0)
        
        for req in requests:
            if req.id != winner.id:
                req.status = "delayed"
                req.result = "DELAYED_CONFLICT"
                req.result_message = f"Delayed due to conflict (prioritized: {winner.id})"
        
        self.db.commit()
        return winner
    
    def _suppress_losers(self, requests: List[AgentRequest], winner: AgentRequest):
        """Mark non-winning requests as suppressed."""
        for req in requests:
            if req.id != winner.id:
                req.status = "suppressed"
                req.result = "MERGED"
                req.result_message = f"Merged into request {winner.id}"
        
        self.db.commit()
    
    def get_merge_recommendation(
        self,
        conflict: Conflict
    ) -> Dict:
        """
        Analyze conflict and recommend merge strategy.
        
        Returns:
            Dictionary with recommendation details
        """
        request_ids = conflict.request_ids
        requests = self.db.query(AgentRequest).filter(
            AgentRequest.id.in_(request_ids)
        ).all()
        
        if not requests:
            return {"error": "No requests found"}
        
        # Analyze requests
        analysis = {
            "conflict_id": str(conflict.id),
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity,
            "request_count": len(requests),
            "requests": [
                {
                    "id": str(r.id),
                    "agent_id": str(r.agent_id),
                    "intent": r.intent,
                    "channel": r.channel,
                    "priority": r.priority,
                    "estimated_value": r.estimated_value,
                    "urgency": r.urgency
                }
                for r in requests
            ],
            "recommended_strategy": self._select_strategy(conflict, requests),
            "alternative_strategies": [
                MergeStrategy.PRIORITIZE_HIGHEST,
                MergeStrategy.PRIORITIZE_VALUE,
                MergeStrategy.SUPPRESS_LOWER
            ]
        }
        
        # Identify likely winner
        recommended_strategy = analysis["recommended_strategy"]
        if recommended_strategy == MergeStrategy.PRIORITIZE_HIGHEST:
            winner = max(requests, key=lambda r: r.priority or 0)
        elif recommended_strategy == MergeStrategy.PRIORITIZE_VALUE:
            winner = max(requests, key=lambda r: r.estimated_value or 0)
        elif recommended_strategy == MergeStrategy.PRIORITIZE_URGENT:
            urgency_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, None: 0}
            winner = max(requests, key=lambda r: urgency_map.get(r.urgency, 0))
        else:
            winner = max(requests, key=lambda r: r.priority or 0)
        
        analysis["likely_winner"] = str(winner.id)
        analysis["reason"] = self._explain_recommendation(recommended_strategy, winner, requests)
        
        return analysis
    
    def _explain_recommendation(
        self,
        strategy: str,
        winner: AgentRequest,
        all_requests: List[AgentRequest]
    ) -> str:
        """Generate human-readable explanation for strategy choice."""
        if strategy == MergeStrategy.PRIORITIZE_HIGHEST:
            return f"Selected highest priority request (priority={winner.priority})"
        elif strategy == MergeStrategy.PRIORITIZE_VALUE:
            return f"Selected highest value request (value=₹{(winner.estimated_value or 0)/100:.2f})"
        elif strategy == MergeStrategy.PRIORITIZE_URGENT:
            return f"Selected most urgent request (urgency={winner.urgency})"
        elif strategy == MergeStrategy.COMBINE_MESSAGES:
            return f"Combining {len(all_requests)} compatible messages"
        elif strategy == MergeStrategy.SUPPRESS_LOWER:
            return f"Suppressing {len(all_requests)-1} lower-priority requests"
        else:
            return f"Using default strategy: {strategy}"
