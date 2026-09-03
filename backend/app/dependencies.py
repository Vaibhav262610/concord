"""
FastAPI dependencies for dependency injection
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Generator

from app.database import SessionLocal
from app.models.agent import Agent
from app.services.auth import AuthService


security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Agent:
    """
    Get current authenticated agent from API key
    
    Usage in route:
        @router.post("/endpoint")
        async def endpoint(agent: Agent = Depends(get_current_agent)):
            # agent is authenticated
    """
    auth_service = AuthService(db)
    agent = auth_service.authenticate_agent(credentials.credentials)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_API_KEY",
                    "message": "Invalid or expired API key"
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return agent


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service instance"""
    return AuthService(db)
