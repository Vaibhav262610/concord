"""
Priority Engine
Rule-based priority scoring for agent requests
"""

from typing import Dict, Any
from datetime import datetime, timedelta

from app.services.arbitration.customer_state import CustomerState


class PriorityEngine:
    """Engine for calculating rule-based priority scores"""
    
    # Base scores by intent (0-100 scale)
    INTENT_BASE_SCORES = {
        "PAYMENT_RECOVERY": 90,      # Highest - payment issues
        "SUBSCRIPTION_RECOVERY": 80,  # High - prevent churn
        "CART_RECOVERY": 70,          # Medium-high - capture revenue
        "WIN_BACK": 50,               # Medium - re-engage
        "UPSELL": 40,                 # Medium-low - grow revenue
        "PROMOTION": 30,              # Low - marketing
        "GENERAL": 50                 # Default
    }
    
    # Urgency multipliers
    URGENCY_MULTIPLIERS = {
        "HIGH": 1.2,
        "MEDIUM": 1.0,
        "LOW": 0.8
    }
    
    def calculate_priority_score(
        self,
        intent: str,
        urgency: str,
        customer_state: CustomerState,
        expires_at: datetime
    ) -> tuple[float, Dict[str, Any]]:
        """
        Calculate rule-based priority score
        
        Args:
            intent: Action intent
            urgency: Urgency level (HIGH, MEDIUM, LOW)
            customer_state: Current customer state
            expires_at: When request expires
        
        Returns:
            Tuple of (score, breakdown_dict)
        """
        breakdown = {}
        
        # 1. Base score from intent (40% of total)
        base_score = self.INTENT_BASE_SCORES.get(intent, 50)
        breakdown["base_score"] = base_score
        breakdown["base_weight"] = 0.4
        
        # 2. Urgency multiplier (20% of total)
        urgency_mult = self.URGENCY_MULTIPLIERS.get(urgency, 1.0)
        urgency_score = base_score * urgency_mult
        breakdown["urgency_multiplier"] = urgency_mult
        breakdown["urgency_score"] = urgency_score
        breakdown["urgency_weight"] = 0.2
        
        # 3. Expiry pressure (20% of total)
        expiry_score = self._calculate_expiry_score(expires_at)
        breakdown["expiry_score"] = expiry_score
        breakdown["expiry_weight"] = 0.2
        
        # 4. Customer engagement (10% of total)
        engagement_score = self._calculate_engagement_score(customer_state)
        breakdown["engagement_score"] = engagement_score
        breakdown["engagement_weight"] = 0.1
        
        # 5. Intent uniqueness (10% of total)
        uniqueness_score = self._calculate_uniqueness_score(customer_state, intent)
        breakdown["uniqueness_score"] = uniqueness_score
        breakdown["uniqueness_weight"] = 0.1
        
        # Calculate weighted total
        total_score = (
            base_score * 0.4 +
            urgency_score * 0.2 +
            expiry_score * 0.2 +
            engagement_score * 0.1 +
            uniqueness_score * 0.1
        )
        
        # Normalize to 0-100
        total_score = max(0, min(100, total_score))
        breakdown["total_score"] = round(total_score, 2)
        
        return total_score, breakdown
    
    def _calculate_expiry_score(self, expires_at: datetime) -> float:
        """
        Score based on how soon request expires
        More urgent as expiry approaches
        """
        now = datetime.now()
        time_left = (expires_at - now).total_seconds() / 3600  # hours
        
        if time_left <= 0:
            return 0  # Already expired
        elif time_left <= 1:
            return 100  # Less than 1 hour - very urgent
        elif time_left <= 6:
            return 80   # Less than 6 hours - urgent
        elif time_left <= 24:
            return 60   # Less than 24 hours - moderate
        elif time_left <= 72:
            return 40   # Less than 3 days - low urgency
        else:
            return 20   # More than 3 days - very low urgency
    
    def _calculate_engagement_score(self, customer_state: CustomerState) -> float:
        """
        Score based on customer engagement history
        Higher score for customers who engage (or need re-engagement)
        """
        # If never contacted before, slightly higher score (new customer)
        if customer_state.last_contact is None:
            return 60
        
        # Calculate days since last contact
        days_since = (datetime.now() - customer_state.last_contact).days
        
        if days_since <= 1:
            return 40  # Just contacted - lower priority
        elif days_since <= 7:
            return 60  # Recent engagement - moderate
        elif days_since <= 30:
            return 70  # Good timing for re-engagement
        elif days_since <= 90:
            return 80  # Needs re-engagement
        else:
            return 90  # High priority to re-engage dormant customer
    
    def _calculate_uniqueness_score(
        self,
        customer_state: CustomerState,
        intent: str
    ) -> float:
        """
        Score based on whether this intent is unique
        Higher score if customer isn't being bombarded with similar intents
        """
        # If this intent is already active, lower score
        if intent in customer_state.active_intents:
            return 30  # Duplicate intent
        
        # If customer has many active intents, lower score
        if len(customer_state.active_intents) >= 3:
            return 40  # Too many competing intents
        elif len(customer_state.active_intents) >= 2:
            return 60  # Some competition
        elif len(customer_state.active_intents) == 1:
            return 80  # One other intent
        else:
            return 100  # No competing intents
