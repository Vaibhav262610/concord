"""
Business Value Engine
Value-based scoring for agent requests
"""

from typing import Dict, Any, Optional
from datetime import datetime

from app.services.arbitration.customer_state import CustomerState


class BusinessValueEngine:
    """Engine for calculating business value scores"""
    
    def calculate_value_score(
        self,
        estimated_value: int,
        urgency: str,
        intent: str,
        customer_state: CustomerState,
        offer: Optional[Dict[str, Any]] = None
    ) -> tuple[float, Dict[str, Any]]:
        """
        Calculate business value score
        
        Args:
            estimated_value: Estimated value in paise
            urgency: Urgency level (HIGH, MEDIUM, LOW)
            intent: Action intent
            customer_state: Current customer state
            offer: Optional offer details
        
        Returns:
            Tuple of (score, breakdown_dict)
        """
        breakdown = {}
        
        # 1. Base value score (50% of total)
        value_score = self._calculate_value_score(estimated_value)
        breakdown["value_score"] = value_score
        breakdown["value_weight"] = 0.5
        breakdown["estimated_value_paise"] = estimated_value
        breakdown["estimated_value_inr"] = estimated_value / 100
        
        # 2. Urgency-adjusted value (20% of total)
        urgency_score = self._calculate_urgency_value(estimated_value, urgency)
        breakdown["urgency_value_score"] = urgency_score
        breakdown["urgency_value_weight"] = 0.2
        
        # 3. Intent value multiplier (15% of total)
        intent_score = self._calculate_intent_value(estimated_value, intent)
        breakdown["intent_value_score"] = intent_score
        breakdown["intent_value_weight"] = 0.15
        
        # 4. Customer lifetime value factor (10% of total)
        ltv_score = self._calculate_ltv_score(customer_state)
        breakdown["ltv_score"] = ltv_score
        breakdown["ltv_weight"] = 0.1
        
        # 5. Offer ROI (5% of total)
        roi_score = self._calculate_roi_score(estimated_value, offer)
        breakdown["roi_score"] = roi_score
        breakdown["roi_weight"] = 0.05
        breakdown["has_offer"] = offer is not None
        
        # Calculate weighted total
        total_score = (
            value_score * 0.5 +
            urgency_score * 0.2 +
            intent_score * 0.15 +
            ltv_score * 0.1 +
            roi_score * 0.05
        )
        
        # Normalize to 0-100
        total_score = max(0, min(100, total_score))
        breakdown["total_score"] = round(total_score, 2)
        
        return total_score, breakdown
    
    def _calculate_value_score(self, estimated_value: int) -> float:
        """
        Score based on estimated value
        Logarithmic scale to handle wide range of values
        """
        if estimated_value <= 0:
            return 0
        
        # Convert paise to rupees for easier thresholds
        value_inr = estimated_value / 100
        
        # Logarithmic scoring
        if value_inr >= 10000:
            return 100  # ₹10,000+ - very high value
        elif value_inr >= 5000:
            return 90   # ₹5,000-10,000 - high value
        elif value_inr >= 2000:
            return 80   # ₹2,000-5,000 - good value
        elif value_inr >= 1000:
            return 70   # ₹1,000-2,000 - moderate value
        elif value_inr >= 500:
            return 60   # ₹500-1,000 - decent value
        elif value_inr >= 200:
            return 50   # ₹200-500 - low-moderate value
        elif value_inr >= 100:
            return 40   # ₹100-200 - low value
        else:
            return 30   # <₹100 - very low value
    
    def _calculate_urgency_value(self, estimated_value: int, urgency: str) -> float:
        """
        Adjust value score based on urgency
        High urgency = higher immediate value
        """
        base_value = self._calculate_value_score(estimated_value)
        
        URGENCY_MULTIPLIERS = {
            "HIGH": 1.3,
            "MEDIUM": 1.0,
            "LOW": 0.7
        }
        
        multiplier = URGENCY_MULTIPLIERS.get(urgency, 1.0)
        return min(100, base_value * multiplier)
    
    def _calculate_intent_value(self, estimated_value: int, intent: str) -> float:
        """
        Adjust value score based on intent
        Different intents have different value realization probabilities
        """
        base_value = self._calculate_value_score(estimated_value)
        
        # Conversion probability by intent
        INTENT_MULTIPLIERS = {
            "PAYMENT_RECOVERY": 1.2,      # High conversion - payment already initiated
            "SUBSCRIPTION_RECOVERY": 1.15, # High conversion - existing customer
            "CART_RECOVERY": 1.0,          # Moderate conversion
            "WIN_BACK": 0.6,               # Low conversion - dormant customer
            "UPSELL": 0.7,                 # Low-moderate conversion
            "PROMOTION": 0.5,              # Low conversion - cold offer
            "GENERAL": 0.8                 # Default
        }
        
        multiplier = INTENT_MULTIPLIERS.get(intent, 0.8)
        return min(100, base_value * multiplier)
    
    def _calculate_ltv_score(self, customer_state: CustomerState) -> float:
        """
        Score based on customer engagement history (proxy for LTV)
        """
        # If never contacted, assume moderate LTV
        if customer_state.last_contact is None:
            return 60
        
        # More contacts = higher engagement = higher LTV proxy
        if customer_state.contacts_today >= 2:
            return 40  # Don't overvalue if already contacted multiple times today
        
        # Use attention budget as engagement proxy
        # Lower remaining budget = more engaged customer
        engagement_level = 100 - customer_state.attention_budget_remaining
        
        if engagement_level >= 80:
            return 90  # Highly engaged
        elif engagement_level >= 60:
            return 80  # Very engaged
        elif engagement_level >= 40:
            return 70  # Moderately engaged
        elif engagement_level >= 20:
            return 60  # Lightly engaged
        else:
            return 50  # Minimal engagement
    
    def _calculate_roi_score(
        self,
        estimated_value: int,
        offer: Optional[Dict[str, Any]]
    ) -> float:
        """
        Score based on ROI if offer is present
        Higher score for better ROI (lower discount relative to value)
        """
        if not offer:
            return 80  # No offer = better ROI
        
        discount_value = offer.get("discount_value", 0)
        
        if estimated_value <= 0 or discount_value <= 0:
            return 80
        
        # Calculate discount percentage
        discount_pct = (discount_value / estimated_value) * 100
        
        if discount_pct >= 50:
            return 30  # Very high discount - poor ROI
        elif discount_pct >= 30:
            return 50  # High discount - moderate ROI
        elif discount_pct >= 20:
            return 60  # Moderate discount - good ROI
        elif discount_pct >= 10:
            return 80  # Low discount - very good ROI
        else:
            return 90  # Minimal discount - excellent ROI
