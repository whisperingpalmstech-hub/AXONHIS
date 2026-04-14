"""accounting_module_manual

Revision ID: f81d819600bc
Revises: aa414c498685
Create Date: 2026-04-14 07:08:50.100128
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f81d819600bc'
down_revision: Union[str, None] = 'aa414c498685'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Chart of Accounts
    op.create_table('accounting_chart_of_accounts',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('account_code', sa.String(length=50), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('parent_account_id', sa.UUID(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_control_account', sa.Boolean(), default=False),
        sa.Column('status', sa.String(length=50), default='ACTIVE'),
        sa.Column('current_balance', sa.Numeric(precision=15, scale=2), default=0.00),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_account_id'], ['accounting_chart_of_accounts.id'])
    )
    op.create_index(op.f('ix_accounting_chart_of_accounts_account_code'), 'accounting_chart_of_accounts', ['account_code'], unique=True)
    
    # 2. Journal Entries Header
    op.create_table('accounting_journal_entries',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('entry_number', sa.String(length=100), nullable=False),
        sa.Column('reference_type', sa.String(length=100), nullable=True),
        sa.Column('reference_id', sa.UUID(), nullable=True),
        sa.Column('entry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), default='DRAFT'),
        sa.Column('total_debit', sa.Numeric(precision=15, scale=2), default=0.00),
        sa.Column('total_credit', sa.Numeric(precision=15, scale=2), default=0.00),
        sa.Column('integration_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('posted_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounting_journal_entries_entry_number'), 'accounting_journal_entries', ['entry_number'], unique=True)

    # 3. Journal Entry Lines
    op.create_table('accounting_journal_entry_lines',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('journal_entry_id', sa.UUID(), nullable=False),
        sa.Column('account_id', sa.UUID(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('debit_amount', sa.Numeric(precision=15, scale=2), default=0.00),
        sa.Column('credit_amount', sa.Numeric(precision=15, scale=2), default=0.00),
        sa.Column('cost_center', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['accounting_journal_entries.id']),
        sa.ForeignKeyConstraint(['account_id'], ['accounting_chart_of_accounts.id'])
    )

def downgrade() -> None:
    op.drop_table('accounting_journal_entry_lines')
    op.drop_index(op.f('ix_accounting_journal_entries_entry_number'), table_name='accounting_journal_entries')
    op.drop_table('accounting_journal_entries')
    op.drop_index(op.f('ix_accounting_chart_of_accounts_account_code'), table_name='accounting_chart_of_accounts')
    op.drop_table('accounting_chart_of_accounts')
