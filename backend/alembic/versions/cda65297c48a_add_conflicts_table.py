"""add_conflicts_table

Revision ID: cda65297c48a
Revises: 001
Create Date: 2026-09-04 01:09:22.562473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cda65297c48a'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conflicts table
    op.create_table(
        'conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.String(100), nullable=False, index=True),
        sa.Column('request_ids', postgresql.JSON, nullable=False),
        sa.Column('agent_ids', postgresql.JSON, nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='detected', index=True),
        sa.Column('resolution_strategy', sa.String(50)),
        sa.Column('merged_request_id', postgresql.UUID(as_uuid=True)),
        sa.Column('conflict_details', postgresql.JSON),
        sa.Column('resolution_metadata', postgresql.JSON),
        sa.Column('detected_at', sa.DateTime, nullable=False, index=True),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create composite indexes
    op.create_index('idx_conflict_customer_status', 'conflicts', ['customer_id', 'status'])
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_conflict_merged_request',
        'conflicts', 'agent_requests',
        ['merged_request_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_table('conflicts')
