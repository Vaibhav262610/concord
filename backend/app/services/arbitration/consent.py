"""
Consent Engine
Enforces global opt-out and consent policies
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.arbitration.customer_state import CustomerState


class ConsentDecision(str, Enum):
    """Consent check result"""
    ALLOWED = "allowed"
    BLOCKED_GLOBAL_OPT_OUT = "blocked_global_opt_out"
    BLOCKED_NO_MARKETING_CONSENT = "blocked_no_marketing_consent"
    BLOCKED_NO_TRANSACTIONAL_CONSENT = "blocked_no_transactional_consent"
    ALLOWED_WITH_WARNING = "allowed_with_warning"


class ConsentEngine:
    """Engine for checking customer consent"""
    
    def check_consent(
        self,
        customer_state: CustomerState,
        intent: str,
        action: str
    ) -> tuple[ConsentDecision, Optional[str]]:
        """
        Check if customer consent allows this action
        
        Args:
            customer_state: Current customer state
            intent: Action intent (PAYMENT_RECOVERY, UPSELL, etc.)
            action: Action type (SEND_MESSAGE, CALL, etc.)
        
        Returns:
            Tuple of (ConsentDecision, reason_message)
        """
        # Global opt-out is absolute - blocks everything
        if customer_state.global_opt_out:
            return (
                ConsentDecision.BLOCKED_GLOBAL_OPT_OUT,
                "Customer has globally opted out of all communications"
            )
        
        # Classify intent as marketing or transactional
        is_marketing = self._is_marketing_intent(intent)
        
        if is_marketing:
            if not customer_state.marketing_consent:
                return (
                    ConsentDecision.BLOCKED_NO_MARKETING_CONSENT,
                    f"Customer has not consented to marketing communications (intent: {intent})"
                )
        else:
            # Transactional intents
            if not customer_state.transactional_consent:
                return (
                    ConsentDecision.BLOCKED_NO_TRANSACTIONAL_CONSENT,
                    f"Customer has not consented to transactional communications (intent: {intent})"
                )
        
        # Check for edge cases that should raise warnings
        warning = self._check_consent_warnings(customer_state, intent, action)
        if warning:
            return (ConsentDecision.ALLOWED_WITH_WARNING, warning)
        
        return (ConsentDecision.ALLOWED, None)
    
    def _is_marketing_intent(self, intent: str) -> bool:
        """
        Determine if intent is marketing or transactional
        
        Marketing: UPSELL, PROMOTION, WIN_BACK
        Transactional: PAYMENT_RECOVERY, SUBSCRIPTION_RECOVERY, CART_RECOVERY
        """
        MARKETING_INTENTS = {
            "UPSELL",
            "PROMOTION",
            "WIN_BACK",
            "CROSS_SELL"
        }
        
        return intent in MARKETING_INTENTS
    
    def _check_consent_warnings(
        self,
        customer_state: CustomerState,
        intent: str,
        action: str
    ) -> Optional[str]:
        """
        Check for consent edge cases that should raise warnings
        
        Returns:
            Warning message if applicable, None otherwise
        """
        # Example: Customer has marketing consent but hasn't been contacted in 6+ months
        # (Might indicate stale consent that should be reconfirmed)
        
        if customer_state.last_contact:
            from datetime import datetime, timedelta
            days_since_contact = (datetime.now() - customer_state.last_contact).days
            
            if days_since_contact > 180 and self._is_marketing_intent(intent):
                return f"Marketing consent may be stale (last contact {days_since_contact} days ago)"
        
        return None
    
    def to_dict(
        self,
        decision: ConsentDecision,
        reason: Optional[str]
    ) -> Dict[str, Any]:
        """Convert consent check result to dictionary"""
        return {
            "decision": decision.value,
            "reason": reason,
            "passed": decision in [ConsentDecision.ALLOWED, ConsentDecision.ALLOWED_WITH_WARNING],
            "is_warning": decision == ConsentDecision.ALLOWED_WITH_WARNING
        }
