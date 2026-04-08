from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompt_mappings.schemas import (
    PromptMappingCreate,
    PromptMappingUpdate,
    PromptMappingResponse,
    PromptVariableCreate,
    PromptVariableResponse,
    PromptExecutionCreate,
    PromptExecutionResponse
)
from app.core.prompt_mappings.services import PromptMappingService
from app.database import get_db

router = APIRouter(prefix="/prompt-mappings", tags=["prompt-mappings"])


@router.post("/mappings", response_model=PromptMappingResponse)
async def create_mapping(
    mapping_data: PromptMappingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prompt mapping."""
    service = PromptMappingService(db)
    mapping = await service.create_mapping(mapping_data)
    return mapping


@router.put("/mappings/{mapping_id}", response_model=PromptMappingResponse)
async def update_mapping(
    mapping_id: UUID,
    update_data: PromptMappingUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing prompt mapping."""
    service = PromptMappingService(db)
    mapping = await service.update_mapping(mapping_id, update_data)
    if not mapping:
        raise HTTPException(status_code=404, detail="Prompt mapping not found")
    return mapping


@router.get("/mappings/{mapping_id}", response_model=PromptMappingResponse)
async def get_mapping(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific prompt mapping."""
    service = PromptMappingService(db)
    mapping = await service.get_mapping(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Prompt mapping not found")
    return mapping


@router.get("/specialties/{specialty_profile_id}/mappings", response_model=List[PromptMappingResponse])
async def get_mappings_by_specialty(
    specialty_profile_id: UUID,
    prompt_category: str = Query(None),
    ui_location: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get prompt mappings for a specialty."""
    service = PromptMappingService(db)
    mappings = await service.get_mappings_by_specialty(
        specialty_profile_id,
        prompt_category,
        ui_location
    )
    return mappings


@router.get("/ui/{ui_location}/mappings", response_model=List[PromptMappingResponse])
async def get_mappings_for_ui(
    ui_location: str,
    specialty_profile_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get prompt mappings for a specific UI location."""
    service = PromptMappingService(db)
    mappings = await service.get_mappings_for_ui(ui_location, specialty_profile_id)
    return mappings


@router.post("/variables", response_model=PromptVariableResponse)
async def create_variable(
    variable_data: PromptVariableCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new prompt variable."""
    service = PromptMappingService(db)
    variable = await service.create_variable(variable_data)
    return variable


@router.get("/variables", response_model=List[PromptVariableResponse])
async def get_variables(
    variable_type: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get prompt variables."""
    service = PromptMappingService(db)
    variables = await service.get_variables(variable_type)
    return variables


@router.post("/execute", response_model=PromptExecutionResponse)
async def execute_prompt(
    execution_data: PromptExecutionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Execute a prompt mapping with AI service."""
    from app.core.ai.grok_client import grok_chat
    
    service = PromptMappingService(db)
    
    # Create a simple AI service wrapper
    class AIService:
        async def generate_response(self, prompt: str):
            messages = [{"role": "user", "content": prompt}]
            response = await grok_chat(messages)
            return response
    
    ai_service = AIService()
    execution = await service.execute_prompt(execution_data, ai_service)
    return execution


@router.get("/executions", response_model=List[PromptExecutionResponse])
async def get_execution_history(
    mapping_id: UUID = Query(None),
    encounter_id: UUID = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get prompt execution history."""
    service = PromptMappingService(db)
    executions = await service.get_execution_history(mapping_id, encounter_id, limit)
    return executions
