"""merge_heads

Revision ID: 67763a9fa5db
Revises: clinical_encounter_flow, fix_qa_test_result
Create Date: 2026-04-13 09:31:26.168906
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67763a9fa5db'
down_revision: Union[str, None] = ('clinical_encounter_flow', 'fix_qa_test_result')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
