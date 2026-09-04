"""
Base Channel Provider
Abstract base class for all communication channel integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ChannelType(str, Enum):
    """Supported channel types"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"
    IN_APP = "IN_APP"


class SendResult:
    """Result of a send operation"""
    
    def __init__(
        self,
        success: bool,
        provider_message_id: Optional[str] = None,
        status: str = "pending",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.provider_message_id = provider_message_id
        self.status = status
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "provider_message_id": self.provider_message_id,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class MessagePayload:
    """Generic message payload for any channel"""
    recipient: str  # Email, phone, user_id, etc.
    subject: Optional[str] = None  # For email
    body: str = ""
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Offer details if present
    offer_type: Optional[str] = None
    offer_value: Optional[float] = None
    offer_code: Optional[str] = None


class BaseChannelProvider(ABC):
    """Abstract base class for channel providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.channel_type: ChannelType = ChannelType.EMAIL  # Override in subclasses
    
    @abstractmethod
    async def send(self, payload: MessagePayload) -> SendResult:
        """
        Send a message through this channel
        
        Args:
            payload: Message payload
        
        Returns:
            SendResult with status
        """
        pass
    
    @abstractmethod
    async def get_status(self, provider_message_id: str) -> Dict[str, Any]:
        """
        Get delivery status from provider
        
        Args:
            provider_message_id: Provider-specific message ID
        
        Returns:
            Status dictionary
        """
        pass
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient format
        
        Args:
            recipient: Recipient identifier
        
        Returns:
            True if valid
        """
        # Override in subclasses for channel-specific validation
        return bool(recipient)
    
    def format_message(self, payload: MessagePayload) -> str:
        """
        Format message for this channel
        
        Args:
            payload: Message payload
        
        Returns:
            Formatted message string
        """
        # Override in subclasses for channel-specific formatting
        return payload.body
    
    def get_channel_limits(self) -> Dict[str, int]:
        """
        Get channel-specific limits
        
        Returns:
            Dictionary of limits (e.g., max_length, rate_limit)
        """
        return {
            "max_message_length": 1000,
            "max_subject_length": 100,
            "rate_limit_per_second": 10
        }
