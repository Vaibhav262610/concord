"""
Push Notification Provider
Mock implementation for MVP - simulates mobile push notifications
In production, integrate with Firebase FCM, APNs, OneSignal, etc.
"""

import asyncio
import uuid
from typing import Dict, Any

from app.services.channels.base import (
    BaseChannelProvider,
    ChannelType,
    MessagePayload,
    SendResult
)


class PushProvider(BaseChannelProvider):
    """Mock push notification provider for MVP"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.channel_type = ChannelType.PUSH
        self.app_id = config.get("app_id", "com.concord.app") if config else "com.concord.app"
    
    async def send(self, payload: MessagePayload) -> SendResult:
        """
        Send push notification (mock implementation)
        
        In production, this would call:
        - Firebase Cloud Messaging (FCM)
        - Apple Push Notification Service (APNs)
        - OneSignal
        - Pusher
        etc.
        """
        # Validate device token
        if not self.validate_recipient(payload.recipient):
            return SendResult(
                success=False,
                status="failed",
                error=f"Invalid device token: {payload.recipient}"
            )
        
        # Simulate API call delay
        await asyncio.sleep(0.05)
        
        # Generate mock message ID
        message_id = f"push_{uuid.uuid4().hex[:16]}"
        
        # Mock success (88% success rate - devices may be offline)
        import random
        if random.random() < 0.88:
            return SendResult(
                success=True,
                provider_message_id=message_id,
                status="sent",
                metadata={
                    "channel": "push",
                    "app_id": self.app_id,
                    "device_token": payload.recipient[:20] + "...",
                    "title": payload.subject,
                    "sent_at": "2026-09-03T12:00:00Z"
                }
            )
        else:
            # Mock failure
            return SendResult(
                success=False,
                provider_message_id=message_id,
                status="failed",
                error="Device offline or token invalid"
            )
    
    async def get_status(self, provider_message_id: str) -> Dict[str, Any]:
        """Get push notification status (mock)"""
        return {
            "message_id": provider_message_id,
            "status": "delivered",
            "delivered_at": "2026-09-03T12:00:01Z",
            "clicked": False
        }
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate device token (simplified)"""
        # Device tokens are typically 64+ char hex strings or base64
        return len(recipient) >= 20
    
    def format_message(self, payload: MessagePayload) -> str:
        """Format push notification"""
        # Push notifications have title + body structure
        notification = {
            "title": payload.subject or "Notification",
            "body": payload.body[:200],  # Keep it concise
            "data": payload.metadata or {}
        }
        
        if payload.offer_type:
            notification["data"]["offer_type"] = payload.offer_type
            notification["data"]["offer_code"] = payload.offer_code
        
        return str(notification)
    
    def get_channel_limits(self) -> Dict[str, int]:
        return {
            "max_message_length": 200,  # Push body should be short
            "max_subject_length": 50,   # Push title should be very short
            "rate_limit_per_second": 100  # Push can handle high throughput
        }
