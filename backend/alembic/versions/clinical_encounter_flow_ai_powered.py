"""Clinical Encounter Flow - AI-Powered Interactive Consultation

Revision ID: clinical_encounter_flow
Revises: 
Create Date: 2026-04-09

This migration adds tables for the complete AI-powered clinical consultation workflow:
- Interactive questioning (one question at a time)
- Examination phase transition
- Management plan generation
- Document generation from audio
- Specialty and doctor-level prompt management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'clinical_encounter_flow'
down_revision = 'add_pharmacy_walkin_age'
branch_labels = None
depends_on = None


def upgrade():
    # Create clinical_encounter_flow table
    op.create_table(
        'clinical_encounter_flow',
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clinician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('specialty_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_phase', sa.String(50), nullable=False, server_default='COMPLAINT_CAPTURE'),
        sa.Column('phase_history', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('chief_complaint_transcript', sa.Text(), nullable=True),
        sa.Column('chief_complaint_language', sa.String(10), nullable=True),
        sa.Column('chief_complaint_analyzed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('adequate_questions_reached', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('examination_findings_transcript', sa.Text(), nullable=True),
        sa.Column('examination_guidance_shown', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('management_plan_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('management_plan_accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('selected_document_types', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('documents_generated', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['encounter_id'], ['md_encounter.encounter_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['md_patient.patient_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['specialty_profile_id'], ['md_specialty_profile.specialty_profile_id']),
    )
    op.create_index('idx_clinical_flow_phase', 'clinical_encounter_flow', ['current_phase', 'started_at'])
    op.create_index('idx_clinical_flow_clinician', 'clinical_encounter_flow', ['clinician_id', 'current_phase'])
    op.create_index('ix_clinical_encounter_flow_encounter_id', 'clinical_encounter_flow', ['encounter_id'], unique=True)

    # Create question_turn table
    op.create_table(
        'question_turn',
        sa.Column('turn_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('llm_question', sa.Text(), nullable=False),
        sa.Column('question_context', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('response_transcript', sa.Text(), nullable=True),
        sa.Column('response_language', sa.String(10), nullable=True),
        sa.Column('response_audio_uri', sa.String(500), nullable=True),
        sa.Column('response_analysis', postgresql.JSONB, nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('suggested_next_action', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['flow_id'], ['clinical_encounter_flow.flow_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['encounter_id'], ['md_encounter.encounter_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_question_turn_flow', 'question_turn', ['flow_id', 'turn_number'])

    # Create examination_guidance table
    op.create_table(
        'examination_guidance',
        sa.Column('guidance_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('critical_examinations', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('examination_priorities', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('specific_findings_to_look_for', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('red_flags', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('examination_findings_transcript', sa.Text(), nullable=True),
        sa.Column('examination_findings_analyzed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('structured_findings', postgresql.JSONB, nullable=True),
        sa.Column('shown_to_doctor', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_by_doctor', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['flow_id'], ['clinical_encounter_flow.flow_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['encounter_id'], ['md_encounter.encounter_id'], ondelete='CASCADE'),
    )
    op.create_index('ix_examination_guidance_flow_id', 'examination_guidance', ['flow_id'], unique=True)

    # Create management_plan table
    op.create_table(
        'management_plan',
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_plan', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('original_plan_text', sa.Text(), nullable=True),
        sa.Column('current_plan', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('current_plan_text', sa.Text(), nullable=True),
        sa.Column('suggested_diagnoses', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('suggested_medications', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('suggested_lab_orders', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('suggested_imaging', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('suggested_procedures', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('follow_up_recommendations', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_modified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('modification_notes', sa.Text(), nullable=True),
        sa.Column('orders_created', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('prescriptions_created', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['flow_id'], ['clinical_encounter_flow.flow_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['encounter_id'], ['md_encounter.encounter_id'], ondelete='CASCADE'),
    )
    op.create_index('ix_management_plan_flow_id', 'management_plan', ['flow_id'], unique=True)

    # Create doctor_prompt_override table
    op.create_table(
        'doctor_prompt_override',
        sa.Column('override_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clinician_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('specialty_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('questioning_prompt', sa.Text(), nullable=True),
        sa.Column('examination_prompt', sa.Text(), nullable=True),
        sa.Column('management_plan_prompt', sa.Text(), nullable=True),
        sa.Column('documentation_prompt', sa.Text(), nullable=True),
        sa.Column('prompt_variables', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('question_style', sa.String(50), nullable=True),
        sa.Column('examination_style', sa.String(50), nullable=True),
        sa.Column('management_style', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['specialty_profile_id'], ['md_specialty_profile.specialty_profile_id']),
    )
    op.create_index('ix_doctor_prompt_override_clinician_id', 'doctor_prompt_override', ['clinician_id'], unique=True)
    op.create_index('idx_doctor_prompt_specialty', 'doctor_prompt_override', ['specialty_profile_id', 'is_active'])


def downgrade():
    op.drop_index('idx_doctor_prompt_specialty', table_name='doctor_prompt_override')
    op.drop_index('ix_doctor_prompt_override_clinician_id', table_name='doctor_prompt_override')
    op.drop_table('doctor_prompt_override')
    
    op.drop_index('ix_management_plan_flow_id', table_name='management_plan')
    op.drop_table('management_plan')
    
    op.drop_index('ix_examination_guidance_flow_id', table_name='examination_guidance')
    op.drop_table('examination_guidance')
    
    op.drop_index('idx_question_turn_flow', table_name='question_turn')
    op.drop_table('question_turn')
    
    op.drop_index('ix_clinical_encounter_flow_encounter_id', table_name='clinical_encounter_flow')
    op.drop_index('idx_clinical_flow_clinician', table_name='clinical_encounter_flow')
    op.drop_index('idx_clinical_flow_phase', table_name='clinical_encounter_flow')
    op.drop_table('clinical_encounter_flow')
