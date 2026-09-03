"""
Decision Engine
Orchestrates all arbitration checks and makes ALLOW/BLOCK/DELAY decisions
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from app.models.agent_request import AgentRequest
from app.services.arbitration.customer_state import CustomerStateService, CustomerState
from app.services.arbitration.consent import ConsentEngine, ConsentDecision
from app.services.arbitration.frequency import FrequencyEngine, FrequencyDecision
from app.services.arbitration.priority import PriorityEngine
from app.services.arbitration.business_value import BusinessValueEngine
from app.services.arbitration.policy import PolicyEngine
from app.services.arbitration.offer_validator import OfferValidator


class DecisionType(str, Enum):
    """Final decision types"""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    DELAY = "DELAY"


class BlockReason(str, Enum):
    """Standardized block reasons"""
    GLOBAL_OPT_OUT = "global_opt_out"
    NO_CONSENT = "no_consent"
    DAILY_LIMIT = "daily_limit_exceeded"
    ATTENTION_BUDGET = "attention_budget_exceeded"
    POLICY_VIOLATION = "policy_violation"
    INVALID_OFFER = "invalid_offer"
    LOW_PRIORITY = "low_priority_score"
    LOW_VALUE = "low_value_score"
    CHANNEL_NOT_ALLOWED = "channel_not_allowed"
    INTENT_NOT_ALLOWED = "intent_not_allowed"
    EXPIRED = "request_expired"


class DecisionEngine:
    """Main orchestrator for arbitration decisions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.state_service = CustomerStateService(db)
        self.consent_engine = ConsentEngine()
        self.frequency_engine = FrequencyEngine(self.state_service)
        self.priority_engine = PriorityEngine()
        self.value_engine = BusinessValueEngine()
        self.policy_engine = PolicyEngine(db)
        self.offer_validator = OfferValidator()
    
    def make_decision(
        self,
        agent_request: AgentRequest
    ) -> tuple[DecisionType, Dict[str, Any]]:
        """
        Make arbitration decision for an agent request
        
        Args:
            agent_request: AgentRequest instance
        
        Returns:
            Tuple of (DecisionType, decision_details_dict)
        """
        decision_details = {
            "request_id": str(agent_request.id),
            "agent_id": str(agent_request.agent_id),
            "customer_id": str(agent_request.customer_id),
            "intent": agent_request.intent,
            "channel": agent_request.channel,
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Step 1: Load customer state
        customer = agent_request.customer
        merchant = agent_request.agent.merchant
        
        # Step 2: Load policy
        policy = self.policy_engine.get_policy(merchant.id)
        policy_rules = self.policy_engine.extract_policy_rules(policy)
        decision_details["policy_rules"] = policy_rules
        
        customer_state = self.state_service.get_customer_state(
            customer,
            daily_limit=policy_rules["daily_limit"]
        )
        decision_details["customer_state"] = customer_state.to_dict()
        
        # Step 3: Check if request is expired
        if agent_request.expires_at and datetime.now() > agent_request.expires_at:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.EXPIRED
            decision_details["message"] = "Request has expired"
            return (DecisionType.BLOCK, decision_details)
        
        # Step 4: Check consent
        consent_decision, consent_reason = self.consent_engine.check_consent(
            customer_state,
            agent_request.intent,
            agent_request.action
        )
        decision_details["checks"]["consent"] = self.consent_engine.to_dict(
            consent_decision, consent_reason
        )
        
        if consent_decision in [
            ConsentDecision.BLOCKED_GLOBAL_OPT_OUT,
            ConsentDecision.BLOCKED_NO_MARKETING_CONSENT,
            ConsentDecision.BLOCKED_NO_TRANSACTIONAL_CONSENT
        ]:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.GLOBAL_OPT_OUT if consent_decision == ConsentDecision.BLOCKED_GLOBAL_OPT_OUT else BlockReason.NO_CONSENT
            decision_details["message"] = consent_reason
            return (DecisionType.BLOCK, decision_details)
        
        # Step 5: Check policy allowances (channel, intent)
        channel_allowed, channel_reason = self.policy_engine.check_channel_allowed(
            policy_rules, agent_request.channel
        )
        decision_details["checks"]["channel_allowed"] = {
            "allowed": channel_allowed,
            "reason": channel_reason
        }
        
        if not channel_allowed:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.CHANNEL_NOT_ALLOWED
            decision_details["message"] = channel_reason
            return (DecisionType.BLOCK, decision_details)
        
        intent_allowed, intent_reason = self.policy_engine.check_intent_allowed(
            policy_rules, agent_request.intent
        )
        decision_details["checks"]["intent_allowed"] = {
            "allowed": intent_allowed,
            "reason": intent_reason
        }
        
        if not intent_allowed:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.INTENT_NOT_ALLOWED
            decision_details["message"] = intent_reason
            return (DecisionType.BLOCK, decision_details)
        
        # Step 6: Validate offer if present
        if agent_request.offer:
            offer_valid, offer_errors = self.offer_validator.validate_offer(
                agent_request.offer,
                policy_rules,
                agent_request.estimated_value
            )
            decision_details["checks"]["offer_validation"] = self.offer_validator.to_dict(
                offer_valid, offer_errors
            )
            
            if not offer_valid:
                decision_details["decision"] = DecisionType.BLOCK
                decision_details["block_reason"] = BlockReason.INVALID_OFFER
                decision_details["message"] = f"Offer validation failed: {offer_errors[0].message}"
                return (DecisionType.BLOCK, decision_details)
        
        # Step 7: Check frequency limits
        freq_decision, freq_reason, attention_cost = self.frequency_engine.check_frequency(
            customer_state,
            agent_request.intent,
            policy_rules["daily_limit"]
        )
        decision_details["checks"]["frequency"] = self.frequency_engine.to_dict(
            freq_decision, freq_reason, attention_cost
        )
        
        if freq_decision in [FrequencyDecision.BLOCKED_DAILY_LIMIT, FrequencyDecision.BLOCKED_ATTENTION_BUDGET]:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.DAILY_LIMIT if freq_decision == FrequencyDecision.BLOCKED_DAILY_LIMIT else BlockReason.ATTENTION_BUDGET
            decision_details["message"] = freq_reason
            return (DecisionType.BLOCK, decision_details)
        
        # Step 8: Calculate priority score
        priority_score, priority_breakdown = self.priority_engine.calculate_priority_score(
            agent_request.intent,
            agent_request.urgency,
            customer_state,
            agent_request.expires_at or datetime.now()
        )
        decision_details["checks"]["priority"] = {
            "score": priority_score,
            "breakdown": priority_breakdown
        }
        
        # Step 9: Calculate business value score
        value_score, value_breakdown = self.value_engine.calculate_value_score(
            agent_request.estimated_value,
            agent_request.urgency,
            agent_request.intent,
            customer_state,
            agent_request.offer
        )
        decision_details["checks"]["business_value"] = {
            "score": value_score,
            "breakdown": value_breakdown
        }
        
        # Step 10: Calculate final combined score (60% priority, 40% value)
        final_score = (priority_score * 0.6) + (value_score * 0.4)
        decision_details["final_score"] = round(final_score, 2)
        decision_details["score_weights"] = {
            "priority": 0.6,
            "value": 0.4
        }
        
        # Step 11: Check score thresholds
        threshold_met, threshold_reason = self.policy_engine.check_score_thresholds(
            policy_rules,
            priority_score,
            value_score
        )
        decision_details["checks"]["thresholds"] = {
            "met": threshold_met,
            "reason": threshold_reason
        }
        
        if not threshold_met:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.LOW_PRIORITY if "Priority" in threshold_reason else BlockReason.LOW_VALUE
            decision_details["message"] = threshold_reason
            return (DecisionType.BLOCK, decision_details)
        
        # Step 12: Evaluate custom policy rules
        custom_allowed, custom_reason = self.policy_engine.evaluate_custom_rules(
            policy_rules,
            {
                "intent": agent_request.intent,
                "estimated_value": agent_request.estimated_value,
                "channel": agent_request.channel,
                "urgency": agent_request.urgency
            }
        )
        decision_details["checks"]["custom_rules"] = {
            "allowed": custom_allowed,
            "reason": custom_reason
        }
        
        if not custom_allowed:
            decision_details["decision"] = DecisionType.BLOCK
            decision_details["block_reason"] = BlockReason.POLICY_VIOLATION
            decision_details["message"] = custom_reason
            return (DecisionType.BLOCK, decision_details)
        
        # Step 13: Determine final decision
        # DELAY logic: Low score but not blocked
        if final_score < 60:
            decision_details["decision"] = DecisionType.DELAY
            decision_details["message"] = f"Request delayed - score {final_score:.2f} below optimal threshold"
            decision_details["delay_reason"] = "low_combined_score"
            return (DecisionType.DELAY, decision_details)
        
        # ALLOW: All checks passed
        decision_details["decision"] = DecisionType.ALLOW
        decision_details["message"] = f"Request approved - score {final_score:.2f}"
        
        # Add any warnings
        warnings = []
        if consent_decision == ConsentDecision.ALLOWED_WITH_WARNING:
            warnings.append(consent_reason)
        if freq_decision in [FrequencyDecision.WARNING_HIGH_FREQUENCY, FrequencyDecision.WARNING_LOW_BUDGET]:
            warnings.append(freq_reason)
        
        if warnings:
            decision_details["warnings"] = warnings
        
        return (DecisionType.ALLOW, decision_details)
