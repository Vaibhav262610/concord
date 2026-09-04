"""
Channel Manager
Routes messages to appropriate channel providers
"""

from typing import Dict, Any, Optional

from app.services.channels.base import (
    BaseChannelProvider,
    ChannelType,
    MessagePayload,
    SendResult
)
from app.services.channels.email_provider import EmailProvider
from app.services.channels.sms_provider import SMSProvider
from app.services.channels.whatsapp_provider import WhatsAppProvider
from app.services.channels.push_provider import PushProvider


class ChannelManager:
    """Manages all channel providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._providers: Dict[str, BaseChannelProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all channel providers"""
        self._providers[ChannelType.EMAIL.value] = EmailProvider(
            self.config.get("email", {})
        )
        self._providers[ChannelType.SMS.value] = SMSProvider(
            self.config.get("sms", {})
        )
        self._providers[ChannelType.WHATSAPP.value] = WhatsAppProvider(
            self.config.get("whatsapp", {})
        )
        self._providers[ChannelType.PUSH.value] = PushProvider(
            self.config.get("push", {})
        )
    
    def get_provider(self, channel: str) -> Optional[BaseChannelProvider]:
        """
        Get provider for a channel
        
        Args:
            channel: Channel type
        
        Returns:
            Provider instance or None
        """
        return self._providers.get(channel.upper())
    
    async def send(
        self,
        channel: str,
        payload: MessagePayload
    ) -> SendResult:
        """
        Send message through specified channel
        
        Args:
            channel: Channel type (EMAIL, SMS, etc.)
            payload: Message payload
        
        Returns:
            SendResult
        """
        provider = self.get_provider(channel)
        
        if not provider:
            return SendResult(
                success=False,
                status="failed",
                error=f"Unsupported channel: {channel}"
            )
        
        try:
            return await provider.send(payload)
        except Exception as e:
            return SendResult(
                success=False,
                status="failed",
                error=f"Channel send failed: {str(e)}"
            )
    
    async def get_status(
        self,
        channel: str,
        provider_message_id: str
    ) -> Dict[str, Any]:
        """
        Get delivery status from channel provider
        
        Args:
            channel: Channel type
            provider_message_id: Provider message ID
        
        Returns:
            Status dictionary
        """
        provider = self.get_provider(channel)
        
        if not provider:
            return {"error": f"Unsupported channel: {channel}"}
        
        try:
            return await provider.get_status(provider_message_id)
        except Exception as e:
            return {"error": f"Status check failed: {str(e)}"}


# Global channel manager instance
channel_manager = ChannelManager()


__all__ = [
    "ChannelManager",
    "channel_manager",
    "BaseChannelProvider",
    "ChannelType",
    "MessagePayload",
    "SendResult",
    "EmailProvider",
    "SMSProvider",
    "WhatsAppProvider",
    "PushProvider"
]
