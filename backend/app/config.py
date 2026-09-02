"""
Configuration management for CONCORD
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://concord:concord_dev_password@localhost:5432/concord"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # AI/LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Merchant defaults (can be overridden per merchant)
    DEFAULT_DAILY_CONTACT_LIMIT: int = 3
    DEFAULT_MAX_DISCOUNT_PERCENT: int = 10
    
    # Priority defaults
    DEFAULT_PRIORITY_PAYMENT_RECOVERY: int = 100
    DEFAULT_PRIORITY_SUBSCRIPTION_RECOVERY: int = 90
    DEFAULT_PRIORITY_CART_RECOVERY: int = 70
    DEFAULT_PRIORITY_UPSELL: int = 30
    DEFAULT_PRIORITY_PROMOTION: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
