"""
Customer State Service
Tracks customer consent, communication history, and attention budget
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import Dict, Any, Optional
import uuid

from app.models.customer import Customer
from app.models.customer_contact import CustomerContact
from app.models.agent_request import AgentRequest


class CustomerState:
    """Customer state snapshot for arbitration"""
    
    def __init__(
        self,
        customer: Customer,
        contacts_today: int,
        last_contact: Optional[datetime],
        active_intents: list[str],
        attention_budget_used: int,
        daily_limit: int
    ):
        self.customer = customer
        self.customer_id = customer.id
        self.contacts_today = contacts_today
        self.last_contact = last_contact
        self.active_intents = active_intents
        self.attention_budget_used = attention_budget_used
        self.attention_budget_remaining = 100 - attention_budget_used  # Out of 100 points
        self.daily_limit = daily_limit
        self.contacts_remaining = max(0, daily_limit - contacts_today)
        
        # Extract consent
        self.consent = customer.consent or {}
        self.marketing_consent = self.consent.get("marketing", False)
        self.transactional_consent = self.consent.get("transactional", True)
        self.global_opt_out = self.consent.get("global_opt_out", False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "customer_id": str(self.customer_id),
            "contacts_today": self.contacts_today,
            "contacts_remaining": self.contacts_remaining,
            "daily_limit": self.daily_limit,
            "last_contact": self.last_contact.isoformat() if self.last_contact else None,
            "active_intents": self.active_intents,
            "attention_budget_used": self.attention_budget_used,
            "attention_budget_remaining": self.attention_budget_remaining,
            "marketing_consent": self.marketing_consent,
            "transactional_consent": self.transactional_consent,
            "global_opt_out": self.global_opt_out
        }


class CustomerStateService:
    """Service for managing customer state"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_state(
        self,
        customer: Customer,
        daily_limit: int = 3
    ) -> CustomerState:
        """
        Get current state for a customer
        
        Args:
            customer: Customer instance
            daily_limit: Daily contact limit (from policy)
        
        Returns:
            CustomerState snapshot
        """
        today = date.today()
        
        # Count contacts today
        contacts_today = self.db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer.id,
            CustomerContact.contact_date == today
        ).count()
        
        # Get last contact time
        last_contact_record = self.db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer.id
        ).order_by(CustomerContact.created_at.desc()).first()
        
        last_contact = last_contact_record.created_at if last_contact_record else None
        
        # Get active intents (pending requests for this customer)
        active_requests = self.db.query(AgentRequest).filter(
            AgentRequest.customer_id == customer.id,
            AgentRequest.status == "pending"
        ).all()
        
        active_intents = list(set(req.intent for req in active_requests))
        
        # Calculate attention budget used today
        # Simple model: each contact consumes points based on intent
        attention_used = self._calculate_attention_used(customer.id, today)
        
        return CustomerState(
            customer=customer,
            contacts_today=contacts_today,
            last_contact=last_contact,
            active_intents=active_intents,
            attention_budget_used=attention_used,
            daily_limit=daily_limit
        )
    
    def _calculate_attention_used(self, customer_id: uuid.UUID, today: date) -> int:
        """
        Calculate attention budget used today
        
        Different intents consume different amounts:
        - PAYMENT_RECOVERY: 20 points
        - SUBSCRIPTION_RECOVERY: 25 points
        - CART_RECOVERY: 30 points
        - UPSELL: 40 points
        - PROMOTION: 50 points
        """
        ATTENTION_COSTS = {
            "PAYMENT_RECOVERY": 20,
            "SUBSCRIPTION_RECOVERY": 25,
            "CART_RECOVERY": 30,
            "WIN_BACK": 35,
            "UPSELL": 40,
            "PROMOTION": 50,
            "GENERAL": 30
        }
        
        contacts = self.db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer_id,
            CustomerContact.contact_date == today
        ).all()
        
        total = sum(ATTENTION_COSTS.get(contact.intent, 30) for contact in contacts)
        return min(total, 100)  # Cap at 100
    
    def record_contact(
        self,
        customer_id: uuid.UUID,
        decision_id: uuid.UUID,
        channel: str,
        intent: str
    ) -> CustomerContact:
        """
        Record a customer contact
        
        Args:
            customer_id: Customer UUID
            decision_id: Decision UUID that approved this contact
            channel: Communication channel
            intent: Intent type
        
        Returns:
            Created CustomerContact record
        """
        contact = CustomerContact(
            customer_id=customer_id,
            decision_id=decision_id,
            contact_date=date.today(),
            channel=channel,
            intent=intent
        )
        
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        return contact
    
    def get_contacts_by_intent(
        self,
        customer_id: uuid.UUID,
        intent: str,
        days: int = 1
    ) -> int:
        """
        Get count of contacts for specific intent in recent days
        
        Args:
            customer_id: Customer UUID
            intent: Intent type
            days: Number of days to look back
        
        Returns:
            Count of contacts
        """
        from datetime import timedelta
        
        cutoff_date = date.today() - timedelta(days=days - 1)
        
        return self.db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer_id,
            CustomerContact.intent == intent,
            CustomerContact.contact_date >= cutoff_date
        ).count()
