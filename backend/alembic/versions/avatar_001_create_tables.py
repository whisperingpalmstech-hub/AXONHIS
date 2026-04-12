"""Avatar tables – sessions, messages, workflow configs

Revision ID: avatar_001
Revises: 90b41a74c0e5
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'avatar_001'
down_revision = '90b41a74c0e5'
branch_labels = ('avatar',)
depends_on = None

def upgrade() -> None:
    op.create_table(
        'avatar_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=True),
        sa.Column('current_workflow', sa.String(50), nullable=True),
        sa.Column('workflow_step', sa.Integer, server_default='0'),
        sa.Column('workflow_data', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'avatar_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True),
                  sa.ForeignKey('avatar_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('workflow', sa.String(50), nullable=True),
        sa.Column('entities', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'avatar_workflow_configs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_key', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_enabled', sa.Boolean, server_default='true', nullable=False),
        sa.Column('icon', sa.String(10), nullable=True),
        sa.Column('system_prompt_override', sa.Text, nullable=True),
        sa.Column('supported_languages', sa.Text, nullable=True),
        sa.Column('display_order', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index('ix_avatar_sessions_user_id', 'avatar_sessions', ['user_id'])
    op.create_index('ix_avatar_sessions_status', 'avatar_sessions', ['status'])
    op.create_index('ix_avatar_sessions_created_at', 'avatar_sessions', ['created_at'])
    op.create_index('ix_avatar_messages_session_id', 'avatar_messages', ['session_id'])
    op.create_index('ix_avatar_messages_created_at', 'avatar_messages', ['created_at'])

def downgrade() -> None:
    op.drop_index('ix_avatar_messages_created_at')
    op.drop_index('ix_avatar_messages_session_id')
    op.drop_index('ix_avatar_sessions_created_at')
    op.drop_index('ix_avatar_sessions_status')
    op.drop_index('ix_avatar_sessions_user_id')
    op.drop_table('avatar_workflow_configs')
    op.drop_table('avatar_messages')
    op.drop_table('avatar_sessions')
