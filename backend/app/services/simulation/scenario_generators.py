"""
Scenario Generators - Generate different test scenarios for simulation
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.simulation.agent_simulators import AgentFleet


class BaseScenario:
    """Base class for scenarios"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.fleet = AgentFleet()
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Generate scenario requests.
        
        Args:
            customer_ids: List of customer IDs to target
            duration_seconds: Duration of simulation in seconds
        
        Returns:
            List of action requests with timing information
        """
        raise NotImplementedError


class HighVolumeScenario(BaseScenario):
    """
    High Volume Scenario
    
    Simulates high traffic with many requests per customer.
    Tests system capacity and rate limiting.
    """
    
    def __init__(self):
        super().__init__(
            name="High Volume",
            description="High traffic with 10-20 requests per customer over 5 minutes"
        )
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        requests = []
        
        for customer_id in customer_ids:
            # Generate 10-20 requests per customer
            num_requests = random.randint(10, 20)
            
            for i in range(num_requests):
                # Spread requests over duration
                time_offset = random.randint(0, duration_seconds)
                
                request = self.fleet.generate_random_request(
                    customer_id,
                    time_offset=time_offset
                )
                
                requests.append(request)
        
        # Sort by time offset
        requests.sort(key=lambda r: r.get("created_at_offset", 0))
        
        return requests


class MixedPriorityScenario(BaseScenario):
    """
    Mixed Priority Scenario
    
    Mix of high and low priority requests.
    Tests priority-based arbitration.
    """
    
    def __init__(self):
        super().__init__(
            name="Mixed Priority",
            description="Mix of high-priority transactional and low-priority marketing"
        )
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        requests = []
        
        agent_weights = {
            "transactional": 0.4,  # High priority
            "payment_recovery": 0.3,  # High priority
            "marketing": 0.2,  # Low priority
            "support": 0.1,
        }
        
        for customer_id in customer_ids:
            # 8-12 requests per customer
            num_requests = random.randint(8, 12)
            
            for i in range(num_requests):
                time_offset = random.randint(0, duration_seconds)
                
                request = self.fleet.generate_random_request(
                    customer_id,
                    time_offset=time_offset,
                    agent_weights=agent_weights
                )
                
                requests.append(request)
        
        requests.sort(key=lambda r: r.get("created_at_offset", 0))
        
        return requests


class ConflictingAgentsScenario(BaseScenario):
    """
    Conflicting Agents Scenario
    
    Multiple agents target same customers simultaneously.
    Tests conflict detection and merge logic.
    """
    
    def __init__(self):
        super().__init__(
            name="Conflicting Agents",
            description="Multiple agents targeting same customers simultaneously"
        )
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        requests = []
        
        # For each customer, create deliberate conflicts
        for customer_id in customer_ids:
            # Create 3-5 conflict windows
            num_conflicts = random.randint(3, 5)
            
            for i in range(num_conflicts):
                # Pick a time for the conflict
                conflict_time = random.randint(0, duration_seconds)
                
                # Generate 2-4 simultaneous requests from different agents
                num_conflicting = random.randint(2, 4)
                agent_types = random.sample(
                    ["payment_recovery", "marketing", "support", "transactional"],
                    num_conflicting
                )
                
                for agent_type in agent_types:
                    # All requests within 30 seconds window (simultaneous)
                    time_offset = conflict_time + random.randint(0, 30)
                    
                    request = self.fleet.generate_request(
                        agent_type,
                        customer_id,
                        time_offset=time_offset
                    )
                    
                    if request:
                        requests.append(request)
        
        requests.sort(key=lambda r: r.get("created_at_offset", 0))
        
        return requests


class RapidFireScenario(BaseScenario):
    """
    Rapid Fire Scenario
    
    Rapid succession of requests.
    Tests frequency limits and attention budget.
    """
    
    def __init__(self):
        super().__init__(
            name="Rapid Fire",
            description="Rapid succession of requests testing frequency limits"
        )
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        requests = []
        
        for customer_id in customer_ids:
            # Create bursts of activity
            num_bursts = random.randint(2, 4)
            
            for burst in range(num_bursts):
                # Pick burst start time
                burst_start = random.randint(0, duration_seconds - 60)
                
                # 5-10 requests in 60 seconds (rapid fire)
                burst_size = random.randint(5, 10)
                
                for i in range(burst_size):
                    time_offset = burst_start + (i * (60 // burst_size))
                    
                    request = self.fleet.generate_random_request(
                        customer_id,
                        time_offset=time_offset
                    )
                    
                    requests.append(request)
        
        requests.sort(key=lambda r: r.get("created_at_offset", 0))
        
        return requests


class MarketingCampaignScenario(BaseScenario):
    """
    Marketing Campaign Scenario
    
    Simulates a marketing campaign blast.
    Tests consent and opt-out logic.
    """
    
    def __init__(self):
        super().__init__(
            name="Marketing Campaign",
            description="Marketing campaign blast to all customers"
        )
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        requests = []
        
        # Campaign blast at start
        campaign_start = random.randint(0, 60)
        
        for customer_id in customer_ids:
            # Initial campaign message
            time_offset = campaign_start + random.randint(0, 30)
            
            request = self.fleet.generate_request(
                "marketing",
                customer_id,
                time_offset=time_offset
            )
            
            if request:
                requests.append(request)
            
            # Follow-up reminder (50% chance)
            if random.random() < 0.5:
                followup_offset = time_offset + random.randint(120, 180)
                if followup_offset < duration_seconds:
                    followup = self.fleet.generate_request(
                        "marketing",
                        customer_id,
                        time_offset=followup_offset
                    )
                    if followup:
                        requests.append(followup)
        
        requests.sort(key=lambda r: r.get("created_at_offset", 0))
        
        return requests


class RealisticMixScenario(BaseScenario):
    """
    Realistic Mix Scenario
    
    Balanced, realistic mix of all agent types.
    Tests overall system behavior.
    """
    
    def __init__(self):
        super().__init__(
            name="Realistic Mix",
            description="Balanced, realistic mix of all agent types and patterns"
        )
    
    def generate(
        self,
        customer_ids: List[str],
        duration_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        requests = []
        
        # Realistic agent distribution
        agent_weights = {
            "transactional": 0.35,  # Most common
            "marketing": 0.30,
            "payment_recovery": 0.20,
            "support": 0.15,
        }
        
        for customer_id in customer_ids:
            # 5-10 requests per customer (realistic)
            num_requests = random.randint(5, 10)
            
            for i in range(num_requests):
                # Requests throughout duration
                time_offset = random.randint(0, duration_seconds)
                
                request = self.fleet.generate_random_request(
                    customer_id,
                    time_offset=time_offset,
                    agent_weights=agent_weights
                )
                
                requests.append(request)
        
        requests.sort(key=lambda r: r.get("created_at_offset", 0))
        
        return requests


class ScenarioFactory:
    """Factory to create and manage scenarios"""
    
    SCENARIOS = {
        "high_volume": HighVolumeScenario,
        "mixed_priority": MixedPriorityScenario,
        "conflicting_agents": ConflictingAgentsScenario,
        "rapid_fire": RapidFireScenario,
        "marketing_campaign": MarketingCampaignScenario,
        "realistic_mix": RealisticMixScenario,
    }
    
    @classmethod
    def get_scenario(cls, scenario_type: str) -> Optional[BaseScenario]:
        """Get scenario by type"""
        scenario_class = cls.SCENARIOS.get(scenario_type)
        if scenario_class:
            return scenario_class()
        return None
    
    @classmethod
    def list_scenarios(cls) -> List[Dict[str, str]]:
        """List all available scenarios"""
        scenarios = []
        for scenario_type, scenario_class in cls.SCENARIOS.items():
            scenario = scenario_class()
            scenarios.append({
                "type": scenario_type,
                "name": scenario.name,
                "description": scenario.description
            })
        return scenarios
    
    @classmethod
    def generate_customers(cls, count: int = 10) -> List[str]:
        """Generate customer IDs for simulation"""
        return [f"SIM_CUST_{i:03d}" for i in range(1, count + 1)]
