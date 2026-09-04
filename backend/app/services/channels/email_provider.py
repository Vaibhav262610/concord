"""
Email Channel Provider
Mock implementation for MVP - simulates email sending
In production, integrate with SendGrid, AWS SES, Mailgun, etc.
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


class EmailProvider(BaseChannelProvider):
    """Mock email provider for MVP"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.channel_type = ChannelType.EMAIL
        self.from_email = config.get("from_email", "noreply@concord.ai") if config else "noreply@concord.ai"
    
    async def send(self, payload: MessagePayload) -> SendResult:
        """
        Send email (mock implementation)
        
        In production, this would call:
        - SendGrid API
        - AWS SES
        - Mailgun
        - Postmark
        etc.
        """
        # Validate email
        if not self.validate_recipient(payload.recipient):
            return SendResult(
                success=False,
                status="failed",
                error=f"Invalid email address: {payload.recipient}"
            )
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Generate mock message ID
        message_id = f"email_{uuid.uuid4().hex[:16]}"
        
        # Mock success (95% success rate)
        import random
        if random.random() < 0.95:
            return SendResult(
                success=True,
                provider_message_id=message_id,
                status="sent",
                metadata={
                    "channel": "email",
                    "from": self.from_email,
                    "to": payload.recipient,
                    "subject": payload.subject,
                    "sent_at": "2026-09-03T12:00:00Z"
                }
            )
        else:
            # Mock failure
            return SendResult(
                success=False,
                provider_message_id=message_id,
                status="failed",
                error="Simulated email delivery failure"
            )
    
    async def get_status(self, provider_message_id: str) -> Dict[str, Any]:
        """Get email delivery status (mock)"""
        # Simulate status check
        return {
            "message_id": provider_message_id,
            "status": "delivered",
            "delivered_at": "2026-09-03T12:00:05Z",
            "opened": False,
            "clicked": False
        }
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate email address"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, recipient))
    
    def format_message(self, payload: MessagePayload) -> str:
        """Format email message"""
        message = f"Subject: {payload.subject}\n\n"
        message += payload.body
        
        if payload.offer_type:
            message += f"\n\n---\nSpecial Offer: {payload.offer_type}"
            if payload.offer_code:
                message += f"\nUse code: {payload.offer_code}"
        
        return message
    
    def get_channel_limits(self) -> Dict[str, int]:
        return {
            "max_message_length": 10000,
            "max_subject_length": 200,
            "rate_limit_per_second": 50
        }
