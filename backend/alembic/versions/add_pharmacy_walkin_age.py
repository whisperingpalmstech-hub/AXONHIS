"""add pharmacy walkin age column

Revision ID: add_pharmacy_walkin_age
Revises: add_missing_md_columns
Create Date: 2026-04-09 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_pharmacy_walkin_age'
down_revision: Union[str, None] = 'add_missing_md_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add walkin_age column to pharmacy_walkin_sales if it doesn't exist
    try:
        op.add_column('pharmacy_walkin_sales', sa.Column('walkin_age', sa.String(10), nullable=True))
    except Exception:
        pass  # Column might already exist


def downgrade():
    try:
        op.drop_column('pharmacy_walkin_sales', 'walkin_age')
    except Exception:
        pass
