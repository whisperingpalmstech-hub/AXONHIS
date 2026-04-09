"""add missing md columns

Revision ID: add_missing_md_columns
Revises: add_diet_prescription
Create Date: 2026-04-09 08:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_missing_md_columns'
down_revision: Union[str, None] = 'add_diet_prescription'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add template_code column to md_document_template_mapping if it doesn't exist
    try:
        op.add_column('md_document_template_mapping', sa.Column('template_code', sa.String(100), nullable=True))
        op.create_index(op.f('ix_md_document_template_mapping_template_code'), 'md_document_template_mapping', ['template_code'], unique=True)
    except Exception:
        pass  # Column might already exist
    
    # Add suggestion_source column to md_suggestion if it doesn't exist
    try:
        op.add_column('md_suggestion', sa.Column('suggestion_source', sa.String(50), nullable=True))
    except Exception:
        pass  # Column might already exist


def downgrade():
    try:
        op.drop_index(op.f('ix_md_document_template_mapping_template_code'), table_name='md_document_template_mapping')
        op.drop_column('md_document_template_mapping', 'template_code')
    except Exception:
        pass
    
    try:
        op.drop_column('md_suggestion', 'suggestion_source')
    except Exception:
        pass
