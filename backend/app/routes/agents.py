"""
API routes for agent management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_auth_service
from app.schemas.agent import AgentCreate, AgentResponse, AgentListResponse, AgentListItem
from app.schemas.error import ErrorResponse
from app.services.auth import AuthService
from app.models.merchant import Merchant


router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Agent created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    }
)
async def register_agent(
    agent_data: AgentCreate,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
):
    """
    Register a new agent
    
    Creates a new agent with generated API key. The API key is returned only once
    and should be stored securely by the caller.
    
    **Important:** Save the returned API key - it cannot be retrieved later!
    
    For this MVP, we'll use a default merchant. In production, this would require
    merchant authentication.
    """
    # Get or create default merchant for MVP
    # In production, merchant_id would come from authenticated merchant session
    merchant = db.query(Merchant).first()
    if not merchant:
        # Create default merchant for MVP
        merchant = Merchant(name="Default Merchant")
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
    
    try:
        # Create agent with API key
        agent, api_key = auth_service.create_agent_with_key(
            merchant_id=merchant.id,
            name=agent_data.name,
            agent_type=agent_data.agent_type,
            description=agent_data.description,
            permissions=agent_data.permissions
        )
        
        return AgentResponse(
            id=str(agent.id),
            name=agent.name,
            agent_type=agent.agent_type,
            api_key=api_key,  # Only time API key is shown!
            permissions=agent.permissions,
            is_active=agent.is_active,
            created_at=agent.created_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "AGENT_CREATION_FAILED",
                    "message": str(e)
                }
            }
        )


@router.get(
    "",
    response_model=AgentListResponse,
    responses={
        200: {"description": "List of agents"},
    }
)
async def list_agents(
    db: Session = Depends(get_db)
):
    """
    List all agents
    
    Returns list of all registered agents for the merchant.
    API keys are not included in the response.
    
    For MVP, this shows all agents. In production, this would be filtered
    by authenticated merchant.
    """
    from app.models.agent import Agent
    
    # In production, filter by merchant_id from authenticated session
    agents = db.query(Agent).all()
    
    return AgentListResponse(
        agents=[
            AgentListItem(
                id=str(agent.id),
                name=agent.name,
                agent_type=agent.agent_type,
                is_active=agent.is_active,
                permissions=agent.permissions,
                created_at=agent.created_at
            )
            for agent in agents
        ],
        total=len(agents)
    )
