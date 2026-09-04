"""
WhatsApp Channel Provider
Mock implementation for MVP - simulates WhatsApp Business API
In production, integrate with Twilio WhatsApp API, Meta WhatsApp Business API, etc.
"""

import asyncio
import re
import uuid
from typing import Dict, Any

from app.services.channels.base import (
    BaseChannelProvider,
    ChannelType,
    MessagePayload,
    SendResult
)


class WhatsAppProvider(BaseChannelProvider):
    """Mock WhatsApp provider for MVP"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.channel_type = ChannelType.WHATSAPP
        self.business_number = config.get("business_number", "+1234567890") if config else "+1234567890"
    
    async def send(self, payload: MessagePayload) -> SendResult:
        """
        Send WhatsApp message (mock implementation)
        
        In production, this would call:
        - Twilio WhatsApp API
        - Meta WhatsApp Business API
        - Gupshup
        - Kaleyra
        etc.
        """
        # Validate phone number
        if not self.validate_recipient(payload.recipient):
            return SendResult(
                success=False,
                status="failed",
                error=f"Invalid WhatsApp number: {payload.recipient}"
            )
        
        # Simulate API call delay
        await asyncio.sleep(0.08)
        
        # Generate mock message ID
        message_id = f"wa_{uuid.uuid4().hex[:16]}"
        
        # Mock success (92% success rate)
        import random
        if random.random() < 0.92:
            return SendResult(
                success=True,
                provider_message_id=message_id,
                status="sent",
                metadata={
                    "channel": "whatsapp",
                    "from": self.business_number,
                    "to": payload.recipient,
                    "template_used": payload.template_id or "default",
                    "sent_at": "2026-09-03T12:00:00Z"
                }
            )
        else:
            # Mock failure
            return SendResult(
                success=False,
                provider_message_id=message_id,
                status="failed",
                error="Simulated WhatsApp delivery failure"
            )
    
    async def get_status(self, provider_message_id: str) -> Dict[str, Any]:
        """Get WhatsApp delivery status (mock)"""
        return {
            "message_id": provider_message_id,
            "status": "delivered",
            "delivered_at": "2026-09-03T12:00:03Z",
            "read": False
        }
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate WhatsApp number (phone number format)"""
        phone = re.sub(r'[^\d+]', '', recipient)
        return bool(re.match(r'^\+?[1-9]\d{9,14}$', phone))
    
    def format_message(self, payload: MessagePayload) -> str:
        """Format WhatsApp message"""
        # WhatsApp supports rich formatting
        message = f"*{payload.subject}*\n\n" if payload.subject else ""
        message += payload.body
        
        if payload.offer_type:
            message += f"\n\n🎁 *Special Offer*: {payload.offer_type}"
            if payload.offer_code:
                message += f"\n📱 *Code*: `{payload.offer_code}`"
        
        return message
    
    def get_channel_limits(self) -> Dict[str, int]:
        return {
            "max_message_length": 4096,  # WhatsApp allows longer messages
            "max_subject_length": 100,
            "rate_limit_per_second": 20
        }
