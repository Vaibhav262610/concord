"""
Webhook Endpoints
Handles delivery status callbacks from channel providers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import logging

from app.dependencies import get_db
from app.services.delivery_tracking import DeliveryTrackingService, DeliveryStatus
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify webhook signature for security
    
    Args:
        payload: Request body bytes
        signature: Signature from header
        secret: Shared secret
    
    Returns:
        True if valid
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post(
    "/delivery/email",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Webhook processed"},
        400: {"model": ErrorResponse, "description": "Invalid webhook"},
        401: {"model": ErrorResponse, "description": "Invalid signature"},
    }
)
async def email_delivery_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Email delivery status webhook
    
    Receives delivery status updates from email providers like:
    - SendGrid
    - AWS SES
    - Mailgun
    - Postmark
    
    For MVP, we accept simple JSON payloads. In production, verify signatures.
    """
    try:
        body = await request.json()
        
        # For MVP, skip signature verification
        # In production: verify_webhook_signature(await request.body(), x_webhook_signature, secret)
        
        execution_id = body.get("execution_id")
        event_type = body.get("event")  # delivered, bounced, failed, opened, clicked
        provider_id = body.get("message_id")
        timestamp = body.get("timestamp")
        error_message = body.get("error")
        
        if not execution_id or not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_WEBHOOK", "message": "Missing required fields"}}
            )
        
        tracking_service = DeliveryTrackingService(db)
        
        # Map event to delivery status
        status_map = {
            "delivered": DeliveryStatus.DELIVERED,
            "bounced": DeliveryStatus.BOUNCED,
            "failed": DeliveryStatus.FAILED,
            "opened": DeliveryStatus.OPENED,
            "clicked": DeliveryStatus.CLICKED
        }
        
        delivery_status = status_map.get(event_type, DeliveryStatus.FAILED)
        
        # Update delivery status
        updated = tracking_service.update_delivery_status(
            execution_id=execution_id,
            status=delivery_status,
            provider_id=provider_id,
            metadata={"event": event_type, "timestamp": timestamp},
            error=error_message
        )
        
        if not updated:
            logger.warning(f"Execution not found for webhook: {execution_id}")
            return {"status": "execution_not_found", "execution_id": execution_id}
        
        logger.info(f"Email webhook processed: {execution_id} -> {event_type}")
        
        return {
            "status": "processed",
            "execution_id": execution_id,
            "event": event_type
        }
    
    except Exception as e:
        logger.error(f"Error processing email webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "WEBHOOK_PROCESSING_FAILED", "message": str(e)}}
        )


@router.post(
    "/delivery/sms",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Webhook processed"},
        400: {"model": ErrorResponse, "description": "Invalid webhook"},
    }
)
async def sms_delivery_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    SMS delivery status webhook
    
    Receives delivery status updates from SMS providers like:
    - Twilio
    - AWS SNS
    - Plivo
    - MSG91
    """
    try:
        body = await request.json()
        
        execution_id = body.get("execution_id")
        status_value = body.get("status")  # delivered, failed, undelivered
        provider_id = body.get("message_sid") or body.get("message_id")
        
        if not execution_id or not status_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_WEBHOOK", "message": "Missing required fields"}}
            )
        
        tracking_service = DeliveryTrackingService(db)
        
        # Map SMS status
        if status_value in ["delivered", "sent"]:
            delivery_status = DeliveryStatus.DELIVERED
        elif status_value in ["failed", "undelivered"]:
            delivery_status = DeliveryStatus.FAILED
        else:
            delivery_status = DeliveryStatus.PENDING
        
        tracking_service.update_delivery_status(
            execution_id=execution_id,
            status=delivery_status,
            provider_id=provider_id,
            metadata={"status": status_value}
        )
        
        logger.info(f"SMS webhook processed: {execution_id} -> {status_value}")
        
        return {
            "status": "processed",
            "execution_id": execution_id,
            "delivery_status": status_value
        }
    
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "WEBHOOK_PROCESSING_FAILED", "message": str(e)}}
        )


@router.post(
    "/delivery/whatsapp",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Webhook processed"},
        400: {"model": ErrorResponse, "description": "Invalid webhook"},
    }
)
async def whatsapp_delivery_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    WhatsApp delivery status webhook
    
    Receives delivery status updates from WhatsApp Business API providers
    """
    try:
        body = await request.json()
        
        execution_id = body.get("execution_id")
        status_value = body.get("status")  # sent, delivered, read, failed
        provider_id = body.get("message_id")
        
        if not execution_id or not status_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_WEBHOOK", "message": "Missing required fields"}}
            )
        
        tracking_service = DeliveryTrackingService(db)
        
        # Map WhatsApp status
        status_map = {
            "sent": DeliveryStatus.SENT,
            "delivered": DeliveryStatus.DELIVERED,
            "read": DeliveryStatus.OPENED,  # WhatsApp "read" = opened
            "failed": DeliveryStatus.FAILED
        }
        
        delivery_status = status_map.get(status_value, DeliveryStatus.PENDING)
        
        tracking_service.update_delivery_status(
            execution_id=execution_id,
            status=delivery_status,
            provider_id=provider_id,
            metadata={"whatsapp_status": status_value}
        )
        
        logger.info(f"WhatsApp webhook processed: {execution_id} -> {status_value}")
        
        return {
            "status": "processed",
            "execution_id": execution_id,
            "delivery_status": status_value
        }
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "WEBHOOK_PROCESSING_FAILED", "message": str(e)}}
        )


@router.post(
    "/delivery/push",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Webhook processed"},
        400: {"model": ErrorResponse, "description": "Invalid webhook"},
    }
)
async def push_delivery_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Push notification delivery webhook
    
    Receives delivery status updates from push notification providers
    """
    try:
        body = await request.json()
        
        execution_id = body.get("execution_id")
        event_type = body.get("event")  # delivered, clicked, dismissed
        provider_id = body.get("notification_id")
        
        if not execution_id or not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_WEBHOOK", "message": "Missing required fields"}}
            )
        
        tracking_service = DeliveryTrackingService(db)
        
        # Map push notification events
        if event_type == "delivered":
            delivery_status = DeliveryStatus.DELIVERED
        elif event_type == "clicked":
            delivery_status = DeliveryStatus.CLICKED
        elif event_type == "failed":
            delivery_status = DeliveryStatus.FAILED
        else:
            delivery_status = DeliveryStatus.SENT
        
        tracking_service.update_delivery_status(
            execution_id=execution_id,
            status=delivery_status,
            provider_id=provider_id,
            metadata={"event": event_type}
        )
        
        logger.info(f"Push webhook processed: {execution_id} -> {event_type}")
        
        return {
            "status": "processed",
            "execution_id": execution_id,
            "event": event_type
        }
    
    except Exception as e:
        logger.error(f"Error processing push webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "WEBHOOK_PROCESSING_FAILED", "message": str(e)}}
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK
)
async def webhook_health():
    """Webhook endpoint health check"""
    return {
        "status": "healthy",
        "endpoints": [
            "/webhooks/delivery/email",
            "/webhooks/delivery/sms",
            "/webhooks/delivery/whatsapp",
            "/webhooks/delivery/push"
        ]
    }
