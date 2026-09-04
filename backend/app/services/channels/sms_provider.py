"""
SMS Channel Provider
Mock implementation for MVP - simulates SMS sending
In production, integrate with Twilio, AWS SNS, Plivo, etc.
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


class SMSProvider(BaseChannelProvider):
    """Mock SMS provider for MVP"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.channel_type = ChannelType.SMS
        self.from_number = config.get("from_number", "+1234567890") if config else "+1234567890"
    
    async def send(self, payload: MessagePayload) -> SendResult:
        """
        Send SMS (mock implementation)
        
        In production, this would call:
        - Twilio API
        - AWS SNS
        - Plivo
        - MSG91 (India-specific)
        etc.
        """
        # Validate phone number
        if not self.validate_recipient(payload.recipient):
            return SendResult(
                success=False,
                status="failed",
                error=f"Invalid phone number: {payload.recipient}"
            )
        
        # Check message length (SMS is limited to 160 chars typically)
        if len(payload.body) > 160:
            return SendResult(
                success=False,
                status="failed",
                error=f"SMS too long: {len(payload.body)} chars (max 160)"
            )
        
        # Simulate API call delay
        await asyncio.sleep(0.05)
        
        # Generate mock message ID
        message_id = f"sms_{uuid.uuid4().hex[:16]}"
        
        # Mock success (90% success rate - SMS has lower deliverability)
        import random
        if random.random() < 0.90:
            return SendResult(
                success=True,
                provider_message_id=message_id,
                status="sent",
                metadata={
                    "channel": "sms",
                    "from": self.from_number,
                    "to": payload.recipient,
                    "message_length": len(payload.body),
                    "sent_at": "2026-09-03T12:00:00Z"
                }
            )
        else:
            # Mock failure
            return SendResult(
                success=False,
                provider_message_id=message_id,
                status="failed",
                error="Simulated SMS delivery failure"
            )
    
    async def get_status(self, provider_message_id: str) -> Dict[str, Any]:
        """Get SMS delivery status (mock)"""
        return {
            "message_id": provider_message_id,
            "status": "delivered",
            "delivered_at": "2026-09-03T12:00:02Z"
        }
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number (basic validation)"""
        # Remove common formatting
        phone = re.sub(r'[^\d+]', '', recipient)
        # Check for valid international format
        return bool(re.match(r'^\+?[1-9]\d{9,14}$', phone))
    
    def format_message(self, payload: MessagePayload) -> str:
        """Format SMS message (keep it short!)"""
        message = payload.body[:140]  # Leave room for offer code
        
        if payload.offer_code:
            message += f"\nCode: {payload.offer_code}"
        
        return message[:160]  # Hard limit
    
    def get_channel_limits(self) -> Dict[str, int]:
        return {
            "max_message_length": 160,
            "max_subject_length": 0,  # SMS doesn't have subject
            "rate_limit_per_second": 10
        }
