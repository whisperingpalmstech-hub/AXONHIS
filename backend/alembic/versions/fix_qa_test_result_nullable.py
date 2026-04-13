"""Make test_definition_id nullable in qa_test_results"""
from alembic import op
import sqlalchemy as sa

revision = 'fix_qa_test_result'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'qa_test_results',
        'test_definition_id',
        existing_type=sa.UUID(),
        nullable=True
    )


def downgrade():
    op.alter_column(
        'qa_test_results',
        'test_definition_id',
        existing_type=sa.UUID(),
        nullable=False
    )
