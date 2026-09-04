"""
Queue Processor
Background worker that processes delayed actions when they're due
"""

import asyncio
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import logging

from app.database import SessionLocal
from app.models.delayed_action import DelayedAction
from app.models.agent_request import AgentRequest
from app.models.decision import Decision

logger = logging.getLogger(__name__)


class QueueProcessor:
    """Background processor for delayed actions"""
    
    def __init__(self):
        self.running = False
        self.poll_interval = 60  # Check every 60 seconds
    
    async def start(self):
        """Start the queue processor"""
        self.running = True
        logger.info("Queue processor started")
        
        while self.running:
            try:
                await self.process_due_actions()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in queue processor: {str(e)}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
    
    async def stop(self):
        """Stop the queue processor"""
        self.running = False
        logger.info("Queue processor stopped")
    
    async def process_due_actions(self):
        """Process all delayed actions that are due"""
        db = SessionLocal()
        
        try:
            # Find all queued actions that are due
            due_actions = db.query(DelayedAction).filter(
                DelayedAction.status == "queued",
                DelayedAction.scheduled_for <= datetime.now()
            ).limit(100).all()  # Process in batches
            
            if due_actions:
                logger.info(f"Processing {len(due_actions)} due actions")
            
            for action in due_actions:
                await self.process_action(db, action)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing due actions: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    async def process_action(self, db: Session, action: DelayedAction):
        """
        Process a single delayed action
        
        Args:
            db: Database session
            action: DelayedAction to process
        """
        try:
            # Load related data
            agent_request = db.query(AgentRequest).filter(
                AgentRequest.id == action.request_id
            ).first()
            
            if not agent_request:
                logger.error(f"Agent request not found for action {action.id}")
                action.status = "failed"
                action.last_error = "Agent request not found"
                return
            
            decision = db.query(Decision).filter(
                Decision.id == action.decision_id
            ).first()
            
            if not decision:
                logger.error(f"Decision not found for action {action.id}")
                action.status = "failed"
                action.last_error = "Decision not found"
                return
            
            # Re-check if customer can still receive this message
            # (In production, this would re-run lightweight checks)
            if not self._can_still_execute(agent_request):
                action.status = "cancelled"
                action.last_error = "Customer no longer eligible (e.g., daily limit reached)"
                logger.info(f"Action {action.id} cancelled - customer not eligible")
                return
            
            # Execute the action
            action.status = "executing"
            db.commit()
            
            # TODO: Call channel provider here
            # For MVP, we simulate execution
            await asyncio.sleep(0.1)  # Simulate API call
            
            # Update status
            action.status = "sent"
            action.executed_at = datetime.now()
            
            # Record contact
            from app.services.arbitration.customer_state import CustomerStateService
            state_service = CustomerStateService(db)
            state_service.record_contact(
                customer_id=agent_request.customer_id,
                decision_id=decision.id,
                channel=agent_request.channel,
                intent=agent_request.intent
            )
            
            logger.info(f"Successfully executed action {action.id}")
            
        except Exception as e:
            logger.error(f"Error processing action {action.id}: {str(e)}", exc_info=True)
            
            # Retry logic
            action.retry_count += 1
            action.last_error = str(e)
            
            if action.retry_count >= 3:
                action.status = "failed"
                logger.error(f"Action {action.id} failed after 3 retries")
            else:
                # Re-queue for retry (add 1 hour)
                from datetime import timedelta
                action.scheduled_for = datetime.now() + timedelta(hours=1)
                action.status = "queued"
                logger.info(f"Action {action.id} re-queued for retry {action.retry_count}")
    
    def _can_still_execute(self, agent_request: AgentRequest) -> bool:
        """
        Check if action can still be executed
        
        This is a lightweight check to avoid re-running full arbitration.
        In production, you might want to re-check critical rules like:
        - Customer hasn't opted out since original decision
        - Daily limit not reached
        - Customer hasn't been contacted very recently
        
        Args:
            agent_request: The agent request
        
        Returns:
            True if can still execute, False otherwise
        """
        # For MVP, always allow
        # In production, add checks here
        return True


# Global processor instance
processor = QueueProcessor()


async def start_queue_processor():
    """Start the background queue processor"""
    await processor.start()


async def stop_queue_processor():
    """Stop the background queue processor"""
    await processor.stop()
