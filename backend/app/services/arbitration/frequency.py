"""
Frequency Engine
Tracks and limits daily customer contacts
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.arbitration.customer_state import CustomerState, CustomerStateService


class FrequencyDecision(str, Enum):
    """Frequency check result"""
    ALLOWED = "allowed"
    BLOCKED_DAILY_LIMIT = "blocked_daily_limit"
    BLOCKED_ATTENTION_BUDGET = "blocked_attention_budget"
    WARNING_HIGH_FREQUENCY = "warning_high_frequency"
    WARNING_LOW_BUDGET = "warning_low_budget"


class FrequencyEngine:
    """Engine for frequency and attention budget checks"""
    
    ATTENTION_COSTS = {
        "PAYMENT_RECOVERY": 20,
        "SUBSCRIPTION_RECOVERY": 25,
        "CART_RECOVERY": 30,
        "WIN_BACK": 35,
        "UPSELL": 40,
        "PROMOTION": 50,
        "GENERAL": 30
    }
    
    def __init__(self, customer_state_service: CustomerStateService):
        self.state_service = customer_state_service
    
    def check_frequency(
        self,
        customer_state: CustomerState,
        intent: str,
        daily_limit: int = 3
    ) -> tuple[FrequencyDecision, Optional[str], int]:
        """
        Check if frequency limits allow this action
        
        Args:
            customer_state: Current customer state
            intent: Action intent
            daily_limit: Daily contact limit (from policy)
        
        Returns:
            Tuple of (FrequencyDecision, reason_message, cost)
        """
        # Calculate cost for this intent
        cost = self.ATTENTION_COSTS.get(intent, 30)
        
        # Check daily limit (hard limit)
        if customer_state.contacts_today >= daily_limit:
            return (
                FrequencyDecision.BLOCKED_DAILY_LIMIT,
                f"Daily limit reached: {customer_state.contacts_today}/{daily_limit} contacts today",
                cost
            )
        
        # Check attention budget (soft limit with cost)
        if customer_state.attention_budget_remaining < cost:
            return (
                FrequencyDecision.BLOCKED_ATTENTION_BUDGET,
                f"Insufficient attention budget: {customer_state.attention_budget_remaining} points remaining, need {cost} points for {intent}",
                cost
            )
        
        # Warnings for approaching limits
        if customer_state.contacts_today >= daily_limit - 1:
            return (
                FrequencyDecision.WARNING_HIGH_FREQUENCY,
                f"Approaching daily limit: {customer_state.contacts_today}/{daily_limit} contacts",
                cost
            )
        
        if customer_state.attention_budget_remaining - cost < 20:
            return (
                FrequencyDecision.WARNING_LOW_BUDGET,
                f"Low attention budget after this contact: {customer_state.attention_budget_remaining - cost} points remaining",
                cost
            )
        
        return (FrequencyDecision.ALLOWED, None, cost)
    
    def check_intent_cooldown(
        self,
        customer_state: CustomerState,
        intent: str,
        cooldown_hours: int = 24
    ) -> tuple[bool, Optional[str]]:
        """
        Check if intent has been used recently (cooldown period)
        
        Args:
            customer_state: Current customer state
            intent: Action intent
            cooldown_hours: Hours to wait between same intent
        
        Returns:
            Tuple of (allowed, reason_message)
        """
        # Check if this intent was used recently
        recent_count = self.state_service.get_contacts_by_intent(
            customer_state.customer_id,
            intent,
            days=1
        )
        
        if recent_count > 0 and customer_state.last_contact:
            hours_since = (datetime.now() - customer_state.last_contact).total_seconds() / 3600
            
            if hours_since < cooldown_hours:
                return (
                    False,
                    f"Intent {intent} used {hours_since:.1f} hours ago, cooldown: {cooldown_hours}h"
                )
        
        return (True, None)
    
    def check_channel_limits(
        self,
        customer_state: CustomerState,
        channel: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check channel-specific limits
        
        Args:
            customer_state: Current customer state
            channel: Communication channel (SMS, EMAIL, WHATSAPP, PUSH, CALL)
        
        Returns:
            Tuple of (allowed, reason_message)
        """
        CHANNEL_LIMITS = {
            "SMS": 2,        # Max 2 SMS per day
            "CALL": 1,       # Max 1 call per day
            "WHATSAPP": 3,   # Max 3 WhatsApp per day
            "EMAIL": 5,      # Max 5 emails per day
            "PUSH": 5        # Max 5 push notifications per day
        }
        
        limit = CHANNEL_LIMITS.get(channel, 3)
        
        # Count channel uses today (would need channel tracking in CustomerContact)
        # For now, return simple check
        if customer_state.contacts_today >= limit:
            return (
                False,
                f"Channel {channel} limit reached: {limit} contacts allowed per day"
            )
        
        return (True, None)
    
    def to_dict(
        self,
        decision: FrequencyDecision,
        reason: Optional[str],
        cost: int
    ) -> Dict[str, Any]:
        """Convert frequency check result to dictionary"""
        return {
            "decision": decision.value,
            "reason": reason,
            "cost": cost,
            "passed": decision in [FrequencyDecision.ALLOWED, FrequencyDecision.WARNING_HIGH_FREQUENCY, FrequencyDecision.WARNING_LOW_BUDGET],
            "is_warning": decision in [FrequencyDecision.WARNING_HIGH_FREQUENCY, FrequencyDecision.WARNING_LOW_BUDGET]
        }
