"""
Policy Engine
Loads and enforces merchant policies
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid

from app.models.policy import Policy


class PolicyEngine:
    """Engine for loading and enforcing merchant policies"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_policy(self, merchant_id: uuid.UUID) -> Optional[Policy]:
        """
        Get merchant policy
        
        Args:
            merchant_id: Merchant UUID
        
        Returns:
            Policy or None
        """
        return self.db.query(Policy).filter(
            Policy.merchant_id == merchant_id,
            Policy.is_active == True
        ).first()
    
    def extract_policy_rules(self, policy: Policy) -> Dict[str, Any]:
        """
        Extract policy rules into structured format
        
        Args:
            policy: Policy instance
        
        Returns:
            Dictionary of policy rules
        """
        if not policy:
            return self._get_default_policy()
        
        rules = policy.config or {}
        
        return {
            "daily_limit": rules.get("daily_limit", 3),
            "cooldown_hours": rules.get("cooldown_hours", 24),
            "max_discount_pct": rules.get("max_discount_pct", 30),
            "max_discount_value": rules.get("max_discount_value", 500000),  # 5000 INR in paise
            "allowed_channels": rules.get("allowed_channels", ["EMAIL", "SMS", "WHATSAPP", "PUSH"]),
            "allowed_intents": rules.get("allowed_intents", [
                "PAYMENT_RECOVERY",
                "SUBSCRIPTION_RECOVERY",
                "CART_RECOVERY",
                "WIN_BACK",
                "UPSELL",
                "PROMOTION"
            ]),
            "priority_threshold": rules.get("priority_threshold", 50),
            "value_threshold": rules.get("value_threshold", 0),
            "require_consent_marketing": rules.get("require_consent_marketing", True),
            "require_consent_transactional": rules.get("require_consent_transactional", False),
            "enable_attention_budget": rules.get("enable_attention_budget", True),
            "custom_rules": rules.get("custom_rules", {})
        }
    
    def _get_default_policy(self) -> Dict[str, Any]:
        """Get default policy if merchant has no custom policy"""
        return {
            "daily_limit": 3,
            "cooldown_hours": 24,
            "max_discount_pct": 30,
            "max_discount_value": 500000,  # 5000 INR in paise
            "allowed_channels": ["EMAIL", "SMS", "WHATSAPP", "PUSH"],
            "allowed_intents": [
                "PAYMENT_RECOVERY",
                "SUBSCRIPTION_RECOVERY",
                "CART_RECOVERY",
                "WIN_BACK",
                "UPSELL",
                "PROMOTION"
            ],
            "priority_threshold": 50,
            "value_threshold": 0,
            "require_consent_marketing": True,
            "require_consent_transactional": False,
            "enable_attention_budget": True,
            "custom_rules": {}
        }
    
    def check_channel_allowed(
        self,
        policy_rules: Dict[str, Any],
        channel: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if channel is allowed by policy
        
        Args:
            policy_rules: Policy rules dictionary
            channel: Channel name
        
        Returns:
            Tuple of (allowed, reason)
        """
        allowed_channels = policy_rules.get("allowed_channels", [])
        
        if channel not in allowed_channels:
            return (
                False,
                f"Channel {channel} not allowed by policy. Allowed: {', '.join(allowed_channels)}"
            )
        
        return (True, None)
    
    def check_intent_allowed(
        self,
        policy_rules: Dict[str, Any],
        intent: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if intent is allowed by policy
        
        Args:
            policy_rules: Policy rules dictionary
            intent: Intent name
        
        Returns:
            Tuple of (allowed, reason)
        """
        allowed_intents = policy_rules.get("allowed_intents", [])
        
        if intent not in allowed_intents:
            return (
                False,
                f"Intent {intent} not allowed by policy. Allowed: {', '.join(allowed_intents)}"
            )
        
        return (True, None)
    
    def check_score_thresholds(
        self,
        policy_rules: Dict[str, Any],
        priority_score: float,
        value_score: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check if scores meet policy thresholds
        
        Args:
            policy_rules: Policy rules dictionary
            priority_score: Priority score (0-100)
            value_score: Value score (0-100)
        
        Returns:
            Tuple of (allowed, reason)
        """
        priority_threshold = policy_rules.get("priority_threshold", 50)
        value_threshold = policy_rules.get("value_threshold", 0)
        
        if priority_score < priority_threshold:
            return (
                False,
                f"Priority score {priority_score:.2f} below threshold {priority_threshold}"
            )
        
        if value_score < value_threshold:
            return (
                False,
                f"Value score {value_score:.2f} below threshold {value_threshold}"
            )
        
        return (True, None)
    
    def evaluate_custom_rules(
        self,
        policy_rules: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Evaluate custom policy rules
        
        Args:
            policy_rules: Policy rules dictionary
            context: Context dictionary with request details
        
        Returns:
            Tuple of (allowed, reason)
        """
        custom_rules = policy_rules.get("custom_rules", {})
        
        if not custom_rules:
            return (True, None)
        
        # Example custom rule checks
        # In production, this could use a rules engine like Python's rules library
        
        # Rule: Block promotions on weekends
        if custom_rules.get("block_promotions_weekend", False):
            from datetime import datetime
            if context.get("intent") == "PROMOTION" and datetime.now().weekday() >= 5:
                return (False, "Promotions blocked on weekends by custom policy")
        
        # Rule: Require minimum value for certain intents
        min_value_rules = custom_rules.get("min_value_by_intent", {})
        intent = context.get("intent")
        if intent in min_value_rules:
            min_value = min_value_rules[intent]
            if context.get("estimated_value", 0) < min_value:
                return (
                    False,
                    f"Value {context.get('estimated_value')} below minimum {min_value} for {intent}"
                )
        
        return (True, None)
