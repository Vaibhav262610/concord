"""
Authentication service for agent API key verification
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import bcrypt
import secrets
from typing import Optional

from app.models.agent import Agent
from app.models.merchant import Merchant


security = HTTPBearer()


def generate_api_key() -> str:
    """
    Generate a secure API key for an agent
    Format: sk_live_<random_string>
    """
    random_part = secrets.token_urlsafe(24)  # 24 bytes -> ~32 chars base64 -> ~42 total chars
    return f"sk_live_{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage"""
    # Use bcrypt directly instead of passlib
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(api_key.encode('utf-8'), salt).decode('utf-8')


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    try:
        return bcrypt.checkpw(plain_key.encode('utf-8'), hashed_key.encode('utf-8'))
    except Exception:
        return False


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = None
) -> Agent:
    """
    Dependency to get current authenticated agent from API key
    
    Usage in routes:
        agent = Depends(get_current_agent)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "API key authentication required"
                }
            }
        )
    
    api_key = credentials.credentials
    
    if not api_key.startswith("sk_live_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_API_KEY_FORMAT",
                    "message": "API key must start with 'sk_live_'"
                }
            }
        )
    
    # Query all agents and check API key hash
    # Note: In production, consider indexing strategy for performance
    agents = db.query(Agent).filter(Agent.is_active == True).all()
    
    for agent in agents:
        if verify_api_key(api_key, agent.api_key_hash):
            return agent
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_API_KEY",
                "message": "Invalid or expired API key"
            }
        }
    )


def check_agent_permission(agent: Agent, permission: str) -> bool:
    """
    Check if agent has a specific permission
    
    Args:
        agent: Agent instance
        permission: Permission name (e.g., 'messaging', 'discounts')
    
    Returns:
        bool: True if agent has permission
    """
    if not agent.permissions:
        return False
    
    return agent.permissions.get(permission, False)


def require_permission(permission: str):
    """
    Decorator/dependency to require specific permission
    
    Usage:
        @app.post("/endpoint")
        def endpoint(agent: Agent = Depends(require_permission("messaging"))):
            ...
    """
    def permission_checker(agent: Agent) -> Agent:
        if not check_agent_permission(agent, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": f"Agent does not have '{permission}' permission"
                    }
                }
            )
        return agent
    
    return permission_checker


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_agent(self, api_key: str) -> Optional[Agent]:
        """
        Authenticate an agent by API key
        
        Args:
            api_key: Plain text API key
        
        Returns:
            Agent if authenticated, None otherwise
        """
        if not api_key.startswith("sk_live_"):
            return None
        
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()
        
        for agent in agents:
            if verify_api_key(api_key, agent.api_key_hash):
                return agent
        
        return None
    
    def create_agent_with_key(
        self,
        merchant_id: str,
        name: str,
        agent_type: str,
        description: Optional[str],
        permissions: dict
    ) -> tuple[Agent, str]:
        """
        Create a new agent with generated API key
        
        Args:
            merchant_id: Merchant ID
            name: Agent name
            agent_type: Type of agent
            description: Optional description
            permissions: Permission dictionary
        
        Returns:
            Tuple of (Agent, plain_api_key)
        """
        # Generate API key
        api_key = generate_api_key()
        api_key_hash = hash_api_key(api_key)
        
        # Create agent
        agent = Agent(
            merchant_id=merchant_id,
            name=name,
            agent_type=agent_type,
            description=description,
            api_key_hash=api_key_hash,
            permissions=permissions,
            is_active=True
        )
        
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        
        return agent, api_key
    
    def validate_agent_permissions(
        self,
        agent: Agent,
        required_permissions: list[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate agent has all required permissions
        
        Args:
            agent: Agent instance
            required_permissions: List of required permission names
        
        Returns:
            Tuple of (is_valid, missing_permission)
        """
        for permission in required_permissions:
            if not check_agent_permission(agent, permission):
                return False, permission
        
        return True, None
