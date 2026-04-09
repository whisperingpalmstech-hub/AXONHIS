"""add diet prescription model

Revision ID: add_diet_prescription
Revises: a1b2c3d4e5f6
Create Date: 2026-04-09 08:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_diet_prescription'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'ipd_diet_prescriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('admission_number', sa.String(), nullable=False),
        sa.Column('patient_uhid', sa.String(), nullable=False),
        sa.Column('diet_type', sa.String(), nullable=False),
        sa.Column('meal_instructions', sa.Text(), nullable=True),
        sa.Column('allergies', sa.String(), nullable=True),
        sa.Column('prescribed_by', sa.String(), nullable=True),
        sa.Column('prescribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['admission_number'], ['ipd_admission_records.admission_number'], ondelete='CASCADE'),
        sa.UniqueConstraint('admission_number')
    )
    op.create_index(op.f('ix_ipd_diet_prescriptions_org_id'), 'ipd_diet_prescriptions', ['org_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ipd_diet_prescriptions_org_id'), table_name='ipd_diet_prescriptions')
    op.drop_table('ipd_diet_prescriptions')
