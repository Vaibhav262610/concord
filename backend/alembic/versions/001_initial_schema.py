"""Initial schema - all CONCORD tables

Revision ID: 001
Revises: 
Create Date: 2026-09-03 03:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create merchants table
    op.create_table(
        'merchants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_merchants_id'), 'merchants', ['id'], unique=False)

    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_hash')
    )
    op.create_index(op.f('ix_agents_agent_type'), 'agents', ['agent_type'], unique=False)
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    op.create_index(op.f('ix_agents_merchant_id'), 'agents', ['merchant_id'], unique=False)

    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('consent', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_external_id'), 'customers', ['external_id'], unique=False)
    op.create_index(op.f('ix_customers_id'), 'customers', ['id'], unique=False)
    op.create_index(op.f('ix_customers_merchant_id'), 'customers', ['merchant_id'], unique=False)

    # Create policies table
    op.create_table(
        'policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policies_id'), 'policies', ['id'], unique=False)
    op.create_index(op.f('ix_policies_merchant_id'), 'policies', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_policies_policy_type'), 'policies', ['policy_type'], unique=False)

    # Create agent_requests table
    op.create_table(
        'agent_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', sa.String(length=255), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('estimated_value', sa.Integer(), nullable=True),
        sa.Column('urgency', sa.String(length=50), nullable=True),
        sa.Column('offer', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id')
    )
    op.create_index('idx_agent_created', 'agent_requests', ['agent_id', 'created_at'], unique=False)
    op.create_index('idx_customer_created', 'agent_requests', ['customer_id', 'created_at'], unique=False)
    op.create_index('idx_status_created', 'agent_requests', ['status', 'created_at'], unique=False)
    op.create_index(op.f('ix_agent_requests_agent_id'), 'agent_requests', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_requests_created_at'), 'agent_requests', ['created_at'], unique=False)
    op.create_index(op.f('ix_agent_requests_customer_id'), 'agent_requests', ['customer_id'], unique=False)
    op.create_index(op.f('ix_agent_requests_id'), 'agent_requests', ['id'], unique=False)
    op.create_index(op.f('ix_agent_requests_intent'), 'agent_requests', ['intent'], unique=False)
    op.create_index(op.f('ix_agent_requests_merchant_id'), 'agent_requests', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_agent_requests_priority'), 'agent_requests', ['priority'], unique=False)
    op.create_index(op.f('ix_agent_requests_request_id'), 'agent_requests', ['request_id'], unique=False)
    op.create_index(op.f('ix_agent_requests_status'), 'agent_requests', ['status'], unique=False)

    # Create decisions table
    op.create_table(
        'decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason_code', sa.String(length=100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('policy_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('conflicting_requests', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('merged_with', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('merged_message', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('delay_reason', sa.String(length=255), nullable=True),
        sa.Column('executed', sa.String(length=50), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('evaluation_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['request_id'], ['agent_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id')
    )
    op.create_index('idx_customer_decision', 'decisions', ['customer_id', 'decision'], unique=False)
    op.create_index('idx_decision_created', 'decisions', ['decision', 'created_at'], unique=False)
    op.create_index(op.f('ix_decisions_created_at'), 'decisions', ['created_at'], unique=False)
    op.create_index(op.f('ix_decisions_customer_id'), 'decisions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_decisions_decision'), 'decisions', ['decision'], unique=False)
    op.create_index(op.f('ix_decisions_id'), 'decisions', ['id'], unique=False)
    op.create_index(op.f('ix_decisions_reason_code'), 'decisions', ['reason_code'], unique=False)
    op.create_index(op.f('ix_decisions_request_id'), 'decisions', ['request_id'], unique=False)

    # Create customer_contacts table
    op.create_table(
        'customer_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_date', sa.Date(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_date', 'customer_contacts', ['customer_id', 'contact_date'], unique=False)
    op.create_index('idx_customer_date_intent', 'customer_contacts', ['customer_id', 'contact_date', 'intent'], unique=False)
    op.create_index(op.f('ix_customer_contacts_contact_date'), 'customer_contacts', ['contact_date'], unique=False)
    op.create_index(op.f('ix_customer_contacts_customer_id'), 'customer_contacts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_contacts_id'), 'customer_contacts', ['id'], unique=False)
    op.create_index(op.f('ix_customer_contacts_intent'), 'customer_contacts', ['intent'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=True),
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_created', 'audit_logs', ['customer_id', 'created_at'], unique=False)
    op.create_index('idx_entity_created', 'audit_logs', ['entity_type', 'entity_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_customer_id'), 'audit_logs', ['customer_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_decision_id'), 'audit_logs', ['decision_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)

    # Create delayed_actions table
    op.create_table(
        'delayed_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('delay_reason', sa.String(length=255), nullable=False),
        sa.Column('result', sa.String(length=50), nullable=True),
        sa.Column('result_message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['agent_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_expires_status', 'delayed_actions', ['expires_at', 'status'], unique=False)
    op.create_index('idx_scheduled_status', 'delayed_actions', ['scheduled_at', 'status'], unique=False)
    op.create_index(op.f('ix_delayed_actions_expires_at'), 'delayed_actions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_delayed_actions_id'), 'delayed_actions', ['id'], unique=False)
    op.create_index(op.f('ix_delayed_actions_request_id'), 'delayed_actions', ['request_id'], unique=False)
    op.create_index(op.f('ix_delayed_actions_scheduled_at'), 'delayed_actions', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_delayed_actions_status'), 'delayed_actions', ['status'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('delayed_actions')
    op.drop_table('audit_logs')
    op.drop_table('customer_contacts')
    op.drop_table('decisions')
    op.drop_table('agent_requests')
    op.drop_table('policies')
    op.drop_table('customers')
    op.drop_table('agents')
    op.drop_table('merchants')
