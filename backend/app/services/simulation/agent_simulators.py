"""
Agent Simulators - Simulate different types of autonomous agents
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseAgentSimulator(ABC):
    """Base class for agent simulators"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.request_count = 0
    
    @abstractmethod
    def generate_request(self, customer_id: str, time_offset: int = 0) -> Dict[str, Any]:
        """
        Generate a simulated action request.
        
        Args:
            customer_id: Target customer ID
            time_offset: Seconds to offset from current time
        
        Returns:
            Dict representing an action request
        """
        pass
    
    def _base_request(
        self,
        customer_id: str,
        action: str,
        intent: str,
        channel: str,
        time_offset: int = 0
    ) -> Dict[str, Any]:
        """Generate base request structure"""
        self.request_count += 1
        
        return {
            "request_id": f"sim_{self.agent_id}_{self.request_count}_{int(datetime.now().timestamp())}",
            "customer_id": customer_id,
            "action": action,
            "intent": intent,
            "channel": channel,
            "created_at_offset": time_offset,  # For simulation timing
        }


class PaymentRecoveryAgent(BaseAgentSimulator):
    """
    Simulates payment recovery agent.
    
    Behavior:
    - High priority (80-95)
    - High estimated value (₹500-5000)
    - Urgent
    - Prefers EMAIL and SMS
    - May offer discounts
    """
    
    def generate_request(self, customer_id: str, time_offset: int = 0) -> Dict[str, Any]:
        channels = ["EMAIL", "SMS", "WHATSAPP"]
        channel = random.choice(channels)
        
        priority = random.randint(80, 95)
        estimated_value = random.randint(50000, 500000)  # ₹500-5000 in paise
        
        request = self._base_request(
            customer_id,
            action="SEND_MESSAGE",
            intent="PAYMENT_RECOVERY",
            channel=channel,
            time_offset=time_offset
        )
        
        request.update({
            "priority": priority,
            "estimated_value": estimated_value,
            "urgency": "HIGH",
            "message": f"Payment reminder for outstanding amount ₹{estimated_value/100:.2f}. Please settle your dues.",
        })
        
        # 40% chance of offering discount
        if random.random() < 0.4:
            discount_value = random.randint(5, 15)
            request["offer"] = {
                "type": "DISCOUNT",
                "value": discount_value,
                "unit": "PERCENT",
            }
            request["message"] += f" Pay now and get {discount_value}% off!"
        
        return request


class MarketingAgent(BaseAgentSimulator):
    """
    Simulates marketing agent.
    
    Behavior:
    - Medium priority (40-70)
    - Variable value (₹100-2000)
    - Low-Medium urgency
    - Uses all channels
    - Often includes offers
    """
    
    def generate_request(self, customer_id: str, time_offset: int = 0) -> Dict[str, Any]:
        channels = ["EMAIL", "SMS", "WHATSAPP", "PUSH"]
        channel = random.choice(channels)
        
        priority = random.randint(40, 70)
        estimated_value = random.randint(10000, 200000)  # ₹100-2000
        
        urgencies = ["LOW", "MEDIUM"]
        urgency = random.choice(urgencies)
        
        request = self._base_request(
            customer_id,
            action="SEND_MESSAGE",  # Changed from SEND_OFFER to SEND_MESSAGE
            intent="PROMOTION",  # Changed from MARKETING to match enum
            channel=channel,
            time_offset=time_offset
        )
        
        request.update({
            "priority": priority,
            "estimated_value": estimated_value,
            "urgency": urgency,
            "message": "Special offer just for you! Limited time deal.",
        })
        
        # 70% chance of offering discount
        if random.random() < 0.7:
            discount_type = random.choice(["PERCENT", "AMOUNT"])
            
            if discount_type == "PERCENT":
                discount_value = random.randint(10, 30)
                request["message"] += f" Get {discount_value}% off!"
            else:
                discount_value = random.randint(50, 500)  # ₹50-500 (in rupees)
                request["message"] += f" Get ₹{discount_value} off!"
            
            request["offer"] = {
                "type": "DISCOUNT",
                "value": discount_value,
                "unit": discount_type,
            }
        
        return request


class SupportAgent(BaseAgentSimulator):
    """
    Simulates customer support agent.
    
    Behavior:
    - High priority (70-90)
    - Low-medium value (₹0-500)
    - High urgency
    - Prefers EMAIL, SMS for follow-ups
    - No offers
    """
    
    def generate_request(self, customer_id: str, time_offset: int = 0) -> Dict[str, Any]:
        channels = ["EMAIL", "SMS", "WHATSAPP"]
        channel = random.choice(channels)
        
        priority = random.randint(70, 90)
        estimated_value = random.randint(0, 50000)  # ₹0-500
        
        request = self._base_request(
            customer_id,
            action="SEND_MESSAGE",
            intent="GENERAL",  # Changed from SUPPORT to match enum
            channel=channel,
            time_offset=time_offset
        )
        
        messages = [
            "Your support ticket has been updated.",
            "We're here to help! Reply to this message with your query.",
            "Your issue has been resolved. Please confirm.",
            "Thank you for contacting support. We're looking into your request.",
        ]
        
        request.update({
            "priority": priority,
            "estimated_value": estimated_value,
            "urgency": "HIGH",
            "message": random.choice(messages),
        })
        
        return request


class TransactionalAgent(BaseAgentSimulator):
    """
    Simulates transactional/notification agent.
    
    Behavior:
    - Very high priority (85-100)
    - Variable value (₹100-10000)
    - High urgency
    - All channels
    - No offers (pure notifications)
    """
    
    def generate_request(self, customer_id: str, time_offset: int = 0) -> Dict[str, Any]:
        channels = ["EMAIL", "SMS", "WHATSAPP", "PUSH"]
        channel = random.choice(channels)
        
        priority = random.randint(85, 100)
        estimated_value = random.randint(10000, 1000000)  # ₹100-10000
        
        request = self._base_request(
            customer_id,
            action="SEND_MESSAGE",
            intent="GENERAL",  # Changed from TRANSACTIONAL to match enum
            channel=channel,
            time_offset=time_offset
        )
        
        messages = [
            "Your order has been confirmed. Order ID: #12345",
            "Payment successful! Transaction ID: TXN789456",
            "Your delivery is out for delivery. Track: DLV123",
            "Account statement generated. View now.",
            "Password changed successfully. If not you, contact support.",
        ]
        
        request.update({
            "priority": priority,
            "estimated_value": estimated_value,
            "urgency": "HIGH",
            "message": random.choice(messages),
        })
        
        return request


class AgentFleet:
    """Manages a fleet of agent simulators"""
    
    def __init__(self, merchant_id: str = "merchant_sim_001"):
        self.merchant_id = merchant_id
        self.agents: Dict[str, BaseAgentSimulator] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize default agent fleet"""
        self.agents = {
            "payment_recovery": PaymentRecoveryAgent("agent_pr_001", "Payment Recovery Bot"),
            "marketing": MarketingAgent("agent_mk_001", "Marketing Bot"),
            "support": SupportAgent("agent_sp_001", "Support Bot"),
            "transactional": TransactionalAgent("agent_tx_001", "Transactional Bot"),
        }
    
    def get_agent(self, agent_type: str) -> Optional[BaseAgentSimulator]:
        """Get agent by type"""
        return self.agents.get(agent_type)
    
    def get_all_agents(self) -> List[BaseAgentSimulator]:
        """Get all agents in fleet"""
        return list(self.agents.values())
    
    def generate_request(
        self,
        agent_type: str,
        customer_id: str,
        time_offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Generate request from specific agent"""
        agent = self.get_agent(agent_type)
        if not agent:
            return None
        
        return agent.generate_request(customer_id, time_offset)
    
    def generate_random_request(
        self,
        customer_id: str,
        time_offset: int = 0,
        agent_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate request from random agent with optional weighting.
        
        Args:
            customer_id: Target customer
            time_offset: Time offset for simulation
            agent_weights: Dict of agent_type -> weight (defaults to equal)
        """
        if not agent_weights:
            agent_weights = {
                "payment_recovery": 0.3,
                "marketing": 0.4,
                "support": 0.2,
                "transactional": 0.1,
            }
        
        agent_types = list(agent_weights.keys())
        weights = list(agent_weights.values())
        
        agent_type = random.choices(agent_types, weights=weights, k=1)[0]
        return self.generate_request(agent_type, customer_id, time_offset)
    
    def get_fleet_stats(self) -> Dict[str, Any]:
        """Get statistics about the fleet"""
        return {
            "total_agents": len(self.agents),
            "agent_types": list(self.agents.keys()),
            "total_requests_generated": sum(
                agent.request_count for agent in self.agents.values()
            ),
            "by_agent": {
                agent_type: {
                    "name": agent.name,
                    "requests_generated": agent.request_count
                }
                for agent_type, agent in self.agents.items()
            }
        }
