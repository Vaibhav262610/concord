"""
Simulation API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time
import logging

from app.database import get_db
from app.services.simulation import ScenarioFactory, AgentFleet
from app.services.gateway import GatewayService
from app.models.agent import Agent
from app.models.customer import Customer
from app.models.merchant import Merchant

router = APIRouter()
logger = logging.getLogger(__name__)


class SimulationRequest(BaseModel):
    """Request to run a simulation"""
    scenario_type: str = Field(
        ...,
        description="Scenario type to simulate"
    )
    customer_count: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of customers to simulate"
    )
    duration_seconds: int = Field(
        300,
        ge=60,
        le=3600,
        description="Simulation duration in seconds"
    )
    speed_multiplier: float = Field(
        1.0,
        ge=0.1,
        le=100.0,
        description="Speed multiplier (1.0 = real-time, 10.0 = 10x faster)"
    )
    create_customers: bool = Field(
        True,
        description="Create simulated customers if they don't exist"
    )


class SimulationResult(BaseModel):
    """Result of a simulation"""
    simulation_id: str
    scenario_type: str
    scenario_name: str
    customer_count: int
    total_requests: int
    duration_seconds: float
    results: Dict[str, Any]
    metrics: Dict[str, Any]


@router.get("/simulation/scenarios")
def list_scenarios():
    """
    List all available simulation scenarios.
    
    Returns list of scenario types with descriptions.
    """
    return {
        "scenarios": ScenarioFactory.list_scenarios()
    }


@router.post("/simulation/run", response_model=SimulationResult)
async def run_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run a fleet simulation.
    
    Simulates multiple agents interacting with customers according to
    the selected scenario. Returns aggregated results and metrics.
    
    Body:
    - scenario_type: Type of scenario to run
    - customer_count: Number of customers (1-100)
    - duration_seconds: Simulation duration (60-3600s)
    - speed_multiplier: Speed multiplier (0.1-100x)
    - create_customers: Whether to create simulated customers
    """
    import uuid
    from datetime import datetime
    
    # Validate scenario type
    scenario = ScenarioFactory.get_scenario(request.scenario_type)
    if not scenario:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario type: {request.scenario_type}"
        )
    
    simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
    
    logger.info(
        f"Starting simulation {simulation_id}: {scenario.name}, "
        f"{request.customer_count} customers, {request.duration_seconds}s"
    )
    
    # Get or create merchant for simulation
    merchant = db.query(Merchant).filter(Merchant.name == "Simulation Merchant").first()
    if not merchant:
        merchant = Merchant(
            name="Simulation Merchant",
            webhook_url="http://simulation/webhook",
            is_active=True
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
    
    # Get or create simulation agent
    agent = db.query(Agent).filter(
        Agent.name == "Simulation Agent",
        Agent.merchant_id == merchant.id
    ).first()
    
    if not agent:
        agent = Agent(
            merchant_id=merchant.id,
            name="Simulation Agent",
            agent_type="simulation",
            permissions={
                "messaging": True,
                "discounts": True,
                "high_value_discounts": True
            },
            is_active=True
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
    
    # Generate customer IDs
    customer_ids = ScenarioFactory.generate_customers(request.customer_count)
    
    # Create customers if requested
    if request.create_customers:
        for customer_id in customer_ids:
            existing = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not existing:
                customer = Customer(
                    merchant_id=merchant.id,
                    customer_id=customer_id,
                    email=f"{customer_id.lower()}@simulation.test",
                    phone=f"+91900000{customer_id[-4:]}",
                    consent_marketing=True,
                    consent_transactional=True,
                    is_active=True
                )
                db.add(customer)
        db.commit()
    
    # Generate scenario requests
    requests = scenario.generate(customer_ids, request.duration_seconds)
    
    logger.info(f"Generated {len(requests)} requests for simulation")
    
    # Run simulation
    gateway = GatewayService(db)
    
    results = {
        "allow": 0,
        "block": 0,
        "delay": 0,
        "merge": 0,
        "errors": 0,
        "by_agent": {},
        "by_customer": {},
        "decisions": [],
    }
    
    start_time = time.time()
    
    for idx, sim_request in enumerate(requests):
        # Calculate delay based on time_offset and speed_multiplier
        time_offset = sim_request.pop("created_at_offset", 0)
        actual_delay = time_offset / request.speed_multiplier
        
        # Sleep until it's time for this request
        elapsed = time.time() - start_time
        if actual_delay > elapsed:
            time.sleep(actual_delay - elapsed)
        
        try:
            # Process request through gateway
            agent_request, is_duplicate, decision, execution_result = gateway.process_action_request(
                agent,
                sim_request
            )
            
            # Record results
            decision_type = decision.decision_type if decision else "ERROR"
            results[decision_type.lower()] = results.get(decision_type.lower(), 0) + 1
            
            # Track by agent type
            intent = sim_request.get("intent", "UNKNOWN")
            results["by_agent"][intent] = results["by_agent"].get(intent, 0) + 1
            
            # Track by customer
            customer_id = sim_request.get("customer_id")
            results["by_customer"][customer_id] = results["by_customer"].get(customer_id, 0) + 1
            
            # Store decision details (sample first 20)
            if len(results["decisions"]) < 20:
                results["decisions"].append({
                    "request_id": sim_request.get("request_id"),
                    "customer_id": customer_id,
                    "intent": intent,
                    "decision": decision_type,
                    "score": decision.final_score if decision else 0,
                })
        
        except Exception as e:
            logger.error(f"Simulation request error: {str(e)}")
            results["errors"] += 1
        
        # Progress log every 10 requests
        if (idx + 1) % 10 == 0:
            logger.info(f"Simulation progress: {idx + 1}/{len(requests)} requests")
    
    actual_duration = time.time() - start_time
    
    # Calculate metrics
    total_requests = sum([results["allow"], results["block"], results["delay"], results.get("merge", 0), results["errors"]])
    
    metrics = {
        "total_requests": total_requests,
        "requests_per_second": total_requests / actual_duration if actual_duration > 0 else 0,
        "allow_rate": results["allow"] / total_requests if total_requests > 0 else 0,
        "block_rate": results["block"] / total_requests if total_requests > 0 else 0,
        "delay_rate": results["delay"] / total_requests if total_requests > 0 else 0,
        "merge_rate": results.get("merge", 0) / total_requests if total_requests > 0 else 0,
        "error_rate": results["errors"] / total_requests if total_requests > 0 else 0,
        "actual_duration_seconds": actual_duration,
        "speedup": request.duration_seconds / actual_duration if actual_duration > 0 else 0,
    }
    
    logger.info(
        f"Simulation {simulation_id} complete: {total_requests} requests, "
        f"{actual_duration:.2f}s, {metrics['requests_per_second']:.2f} req/s"
    )
    
    return {
        "simulation_id": simulation_id,
        "scenario_type": request.scenario_type,
        "scenario_name": scenario.name,
        "customer_count": request.customer_count,
        "total_requests": total_requests,
        "duration_seconds": actual_duration,
        "results": results,
        "metrics": metrics,
    }


@router.get("/simulation/fleet")
def get_fleet_info():
    """
    Get information about the agent fleet.
    
    Returns details about available agent types and their behaviors.
    """
    fleet = AgentFleet()
    
    agent_info = {
        "payment_recovery": {
            "name": "Payment Recovery Bot",
            "description": "High-priority payment reminders with optional discounts",
            "behavior": {
                "priority": "80-95",
                "estimated_value": "₹500-5000",
                "urgency": "HIGH",
                "channels": ["EMAIL", "SMS", "WHATSAPP"],
                "offers_discounts": "40% chance",
            }
        },
        "marketing": {
            "name": "Marketing Bot",
            "description": "Marketing campaigns and promotional offers",
            "behavior": {
                "priority": "40-70",
                "estimated_value": "₹100-2000",
                "urgency": "LOW-MEDIUM",
                "channels": ["EMAIL", "SMS", "WHATSAPP", "PUSH"],
                "offers_discounts": "70% chance",
            }
        },
        "support": {
            "name": "Support Bot",
            "description": "Customer support follow-ups and ticket updates",
            "behavior": {
                "priority": "70-90",
                "estimated_value": "₹0-500",
                "urgency": "HIGH",
                "channels": ["EMAIL", "SMS", "WHATSAPP"],
                "offers_discounts": "Never",
            }
        },
        "transactional": {
            "name": "Transactional Bot",
            "description": "Critical transactional notifications",
            "behavior": {
                "priority": "85-100",
                "estimated_value": "₹100-10000",
                "urgency": "HIGH",
                "channels": ["EMAIL", "SMS", "WHATSAPP", "PUSH"],
                "offers_discounts": "Never",
            }
        },
    }
    
    return {
        "fleet_stats": fleet.get_fleet_stats(),
        "agent_info": agent_info
    }
