"""
Delivery Tracking Service
Tracks the status of sent messages through their lifecycle
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

from app.models.delayed_action import DelayedAction


class DeliveryStatus(str, Enum):
    """Delivery status types"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    UNSUBSCRIBED = "unsubscribed"


class DeliveryEvent:
    """A delivery status event"""
    
    def __init__(
        self,
        execution_id: uuid.UUID,
        status: DeliveryStatus,
        timestamp: datetime,
        provider_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.execution_id = execution_id
        self.status = status
        self.timestamp = timestamp
        self.provider_id = provider_id
        self.metadata = metadata or {}
        self.error = error


class DeliveryTrackingService:
    """Service for tracking message delivery status"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_delivery_status(
        self,
        execution_id: uuid.UUID,
        status: DeliveryStatus,
        provider_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update delivery status for an execution
        
        Args:
            execution_id: Execution ID
            status: New delivery status
            provider_id: Provider-specific message ID
            metadata: Additional metadata
            error: Error message if failed
        
        Returns:
            True if updated, False if execution not found
        """
        execution = self.db.query(DelayedAction).filter(
            DelayedAction.id == execution_id
        ).first()
        
        if not execution:
            return False
        
        # Update status
        execution.status = status.value
        
        # Update metadata
        if not execution.execution_metadata:
            execution.execution_metadata = {}
        
        execution.execution_metadata.update({
            "delivery_status": status.value,
            "delivery_updated_at": datetime.now().isoformat(),
            "provider_id": provider_id,
            **(metadata or {})
        })
        
        if error:
            execution.last_error = error
        
        # Record status history
        if "status_history" not in execution.execution_metadata:
            execution.execution_metadata["status_history"] = []
        
        execution.execution_metadata["status_history"].append({
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "provider_id": provider_id
        })
        
        self.db.commit()
        return True
    
    def get_delivery_status(
        self,
        execution_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get current delivery status
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Status dictionary or None
        """
        execution = self.db.query(DelayedAction).filter(
            DelayedAction.id == execution_id
        ).first()
        
        if not execution:
            return None
        
        metadata = execution.execution_metadata or {}
        
        return {
            "execution_id": str(execution.id),
            "status": execution.status,
            "delivery_status": metadata.get("delivery_status", execution.status),
            "provider_id": metadata.get("provider_id"),
            "executed_at": execution.executed_at.isoformat() if execution.executed_at else None,
            "delivered_at": metadata.get("delivered_at"),
            "opened_at": metadata.get("opened_at"),
            "clicked_at": metadata.get("clicked_at"),
            "last_error": execution.last_error,
            "status_history": metadata.get("status_history", [])
        }
    
    def get_delivery_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[str] = None,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get delivery metrics for a time period
        
        Args:
            start_date: Start date
            end_date: End date
            channel: Filter by channel
            intent: Filter by intent
        
        Returns:
            Metrics dictionary
        """
        query = self.db.query(DelayedAction).filter(
            DelayedAction.processed_at >= start_date,
            DelayedAction.processed_at <= end_date
        )
        
        # Apply filters via metadata (simplified for MVP)
        executions = query.all()
        
        # Calculate metrics
        total = len(executions)
        sent = sum(1 for e in executions if e.status == "sent")
        delivered = sum(
            1 for e in executions 
            if e.execution_metadata and e.execution_metadata.get("delivery_status") == "delivered"
        )
        failed = sum(1 for e in executions if e.status == "failed")
        bounced = sum(
            1 for e in executions
            if e.execution_metadata and e.execution_metadata.get("delivery_status") == "bounced"
        )
        
        return {
            "total_executions": total,
            "sent": sent,
            "delivered": delivered,
            "failed": failed,
            "bounced": bounced,
            "delivery_rate": (delivered / total * 100) if total > 0 else 0,
            "failure_rate": (failed / total * 100) if total > 0 else 0,
            "bounce_rate": (bounced / total * 100) if total > 0 else 0
        }
    
    def mark_as_delivered(
        self,
        execution_id: uuid.UUID,
        provider_id: str,
        delivered_at: Optional[datetime] = None
    ) -> bool:
        """
        Mark execution as delivered
        
        Args:
            execution_id: Execution ID
            provider_id: Provider message ID
            delivered_at: Delivery timestamp
        
        Returns:
            True if updated
        """
        return self.update_delivery_status(
            execution_id=execution_id,
            status=DeliveryStatus.DELIVERED,
            provider_id=provider_id,
            metadata={
                "delivered_at": (delivered_at or datetime.now()).isoformat()
            }
        )
    
    def mark_as_failed(
        self,
        execution_id: uuid.UUID,
        error: str,
        provider_id: Optional[str] = None
    ) -> bool:
        """
        Mark execution as failed
        
        Args:
            execution_id: Execution ID
            error: Error message
            provider_id: Provider message ID
        
        Returns:
            True if updated
        """
        return self.update_delivery_status(
            execution_id=execution_id,
            status=DeliveryStatus.FAILED,
            provider_id=provider_id,
            error=error
        )
    
    def mark_as_bounced(
        self,
        execution_id: uuid.UUID,
        reason: str,
        provider_id: Optional[str] = None
    ) -> bool:
        """
        Mark execution as bounced
        
        Args:
            execution_id: Execution ID
            reason: Bounce reason
            provider_id: Provider message ID
        
        Returns:
            True if updated
        """
        return self.update_delivery_status(
            execution_id=execution_id,
            status=DeliveryStatus.BOUNCED,
            provider_id=provider_id,
            metadata={"bounce_reason": reason}
        )
    
    def track_engagement(
        self,
        execution_id: uuid.UUID,
        event_type: str,  # "opened", "clicked", "replied"
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track user engagement events
        
        Args:
            execution_id: Execution ID
            event_type: Type of engagement event
            metadata: Additional event data
        
        Returns:
            True if updated
        """
        event_status_map = {
            "opened": DeliveryStatus.OPENED,
            "clicked": DeliveryStatus.CLICKED,
            "replied": DeliveryStatus.REPLIED
        }
        
        status = event_status_map.get(event_type)
        if not status:
            return False
        
        event_metadata = {
            f"{event_type}_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        return self.update_delivery_status(
            execution_id=execution_id,
            status=status,
            metadata=event_metadata
        )
