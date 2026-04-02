"""add cssd module tables

Revision ID: b7c2e4f1a3d9
Revises: fa130d3daacb
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b7c2e4f1a3d9'
down_revision = 'fa130d3daacb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Instrument Sets
    op.create_table('cssd_instrument_sets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('set_code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('instrument_count', sa.Integer(), default=0),
        sa.Column('condition', sa.Enum('serviceable', 'damaged', 'under_repair', 'condemned', name='instrumentcondition'), default='serviceable'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cssd_instrument_sets_name', 'cssd_instrument_sets', ['name'])
    op.create_index('ix_cssd_instrument_sets_set_code', 'cssd_instrument_sets', ['set_code'], unique=True)
    op.create_index('ix_cssd_instrument_sets_org_id', 'cssd_instrument_sets', ['org_id'])

    # Sterilization Cycles
    op.create_table('cssd_sterilization_cycles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cycle_number', sa.String(50), nullable=False),
        sa.Column('machine_id', sa.String(50), nullable=False),
        sa.Column('method', sa.Enum('steam_autoclave', 'eto_gas', 'plasma', 'dry_heat', 'chemical', name='sterilizationmethod'), nullable=False),
        sa.Column('status', sa.Enum('loading', 'in_progress', 'completed', 'failed', 'released', name='cyclestatus'), nullable=False),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('temperature_celsius', sa.Numeric(5, 1), nullable=True),
        sa.Column('pressure_psi', sa.Numeric(5, 1), nullable=True),
        sa.Column('exposure_minutes', sa.Integer(), nullable=True),
        sa.Column('bi_result', sa.String(20), nullable=True),
        sa.Column('ci_result', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cssd_sterilization_cycles_cycle_number', 'cssd_sterilization_cycles', ['cycle_number'], unique=True)
    op.create_index('ix_cssd_sterilization_cycles_org_id', 'cssd_sterilization_cycles', ['org_id'])

    # Cycle-Set Links
    op.create_table('cssd_cycle_set_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['cycle_id'], ['cssd_sterilization_cycles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['set_id'], ['cssd_instrument_sets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cssd_cycle_set_links_cycle_id', 'cssd_cycle_set_links', ['cycle_id'])
    op.create_index('ix_cssd_cycle_set_links_set_id', 'cssd_cycle_set_links', ['set_id'])
    op.create_index('ix_cssd_cycle_set_links_org_id', 'cssd_cycle_set_links', ['org_id'])

    # Dispatches
    op.create_table('cssd_dispatches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cycle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('destination_department', sa.String(100), nullable=False),
        sa.Column('dispatched_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(), nullable=True),
        sa.Column('returned_at', sa.DateTime(), nullable=True),
        sa.Column('return_condition', sa.Enum('serviceable', 'damaged', 'under_repair', 'condemned', name='instrumentcondition', create_type=False), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['set_id'], ['cssd_instrument_sets.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cycle_id'], ['cssd_sterilization_cycles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dispatched_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('cssd_dispatches')
    op.drop_table('cssd_cycle_set_links')
    op.drop_table('cssd_sterilization_cycles')
    op.drop_table('cssd_instrument_sets')
    sa.Enum(name='instrumentcondition').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sterilizationmethod').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='cyclestatus').drop(op.get_bind(), checkfirst=True)
