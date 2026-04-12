from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.core.prompt_mappings.models import (
    MdPromptMapping,
    MdPromptVariable,
    MdPromptExecution
)
from app.core.prompt_mappings.schemas import (
    PromptMappingCreate,
    PromptMappingUpdate,
    PromptVariableCreate,
    PromptExecutionCreate
)


class PromptMappingService:
    """Service for managing prompt mappings for specialty UI."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_mapping(
        self,
        mapping_data: PromptMappingCreate
    ) -> MdPromptMapping:
        """Create a new prompt mapping."""
        mapping = MdPromptMapping(
            specialty_profile_id=mapping_data.specialty_profile_id,
            prompt_category=mapping_data.prompt_category,
            ui_element=mapping_data.ui_element,
            ui_location=mapping_data.ui_location,
            prompt_template=mapping_data.prompt_template,
            prompt_variables=mapping_data.prompt_variables,
            trigger_condition=mapping_data.trigger_condition,
            output_mapping=mapping_data.output_mapping,
            priority=mapping_data.priority,
            created_by=mapping_data.created_by
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def update_mapping(
        self,
        mapping_id: uuid.UUID,
        update_data: PromptMappingUpdate
    ) -> Optional[MdPromptMapping]:
        """Update an existing prompt mapping."""
        query = select(MdPromptMapping).where(
            MdPromptMapping.mapping_id == mapping_id
        )
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            return None
        
        if update_data.prompt_template is not None:
            mapping.prompt_template = update_data.prompt_template
        if update_data.prompt_variables is not None:
            mapping.prompt_variables = update_data.prompt_variables
        if update_data.trigger_condition is not None:
            mapping.trigger_condition = update_data.trigger_condition
        if update_data.output_mapping is not None:
            mapping.output_mapping = update_data.output_mapping
        if update_data.is_active is not None:
            mapping.is_active = update_data.is_active
        if update_data.priority is not None:
            mapping.priority = update_data.priority
        
        mapping.version += 1
        mapping.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def get_mapping(
        self,
        mapping_id: uuid.UUID
    ) -> Optional[MdPromptMapping]:
        """Get a specific prompt mapping."""
        query = select(MdPromptMapping).where(
            MdPromptMapping.mapping_id == mapping_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_mappings_by_specialty(
        self,
        specialty_profile_id: uuid.UUID,
        prompt_category: Optional[str] = None,
        ui_location: Optional[str] = None
    ) -> List[MdPromptMapping]:
        """Get prompt mappings for a specialty."""
        conditions = [
            MdPromptMapping.specialty_profile_id == specialty_profile_id,
            MdPromptMapping.is_active == True
        ]
        
        if prompt_category:
            conditions.append(MdPromptMapping.prompt_category == prompt_category)
        
        if ui_location:
            conditions.append(MdPromptMapping.ui_location == ui_location)
        
        query = select(MdPromptMapping).where(
            and_(*conditions)
        ).order_by(desc(MdPromptMapping.priority), MdPromptMapping.ui_element)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_mappings_for_ui(
        self,
        ui_location: str,
        specialty_profile_id: Optional[uuid.UUID] = None
    ) -> List[MdPromptMapping]:
        """Get prompt mappings for a specific UI location."""
        conditions = [MdPromptMapping.ui_location == ui_location, MdPromptMapping.is_active == True]
        
        if specialty_profile_id:
            conditions.append(MdPromptMapping.specialty_profile_id == specialty_profile_id)
        
        query = select(MdPromptMapping).where(
            and_(*conditions)
        ).order_by(desc(MdPromptMapping.priority))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_variable(
        self,
        variable_data: PromptVariableCreate
    ) -> MdPromptVariable:
        """Create a new prompt variable."""
        variable = MdPromptVariable(
            variable_name=variable_data.variable_name,
            variable_type=variable_data.variable_type,
            description=variable_data.description,
            default_value=variable_data.default_value,
            is_required=variable_data.is_required,
            validation_regex=variable_data.validation_regex
        )
        self.db.add(variable)
        await self.db.commit()
        await self.db.refresh(variable)
        return variable

    async def get_variables(
        self,
        variable_type: Optional[str] = None
    ) -> List[MdPromptVariable]:
        """Get prompt variables."""
        conditions = []
        
        if variable_type:
            conditions.append(MdPromptVariable.variable_type == variable_type)
        
        query = select(MdPromptVariable)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(MdPromptVariable.variable_name)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def execute_prompt(
        self,
        execution_data: PromptExecutionCreate,
        ai_service
    ) -> MdPromptExecution:
        """Execute a prompt mapping with AI service."""
        mapping = await self.get_mapping(execution_data.mapping_id)
        if not mapping:
            raise ValueError("Prompt mapping not found")
        
        # Build prompt with variable substitution
        prompt_text = await self._build_prompt(
            mapping.prompt_template,
            execution_data.input_data
        )
        
        start_time = time.time()
        
        try:
            # Call AI service
            ai_response = await ai_service.generate_response(prompt_text)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            execution = MdPromptExecution(
                mapping_id=execution_data.mapping_id,
                encounter_id=execution_data.encounter_id,
                patient_id=execution_data.patient_id,
                user_id=execution_data.user_id,
                input_data=execution_data.input_data,
                prompt_text=prompt_text,
                ai_response=ai_response,
                execution_time_ms=execution_time,
                status="SUCCESS"
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            execution = MdPromptExecution(
                mapping_id=execution_data.mapping_id,
                encounter_id=execution_data.encounter_id,
                patient_id=execution_data.patient_id,
                user_id=execution_data.user_id,
                input_data=execution_data.input_data,
                prompt_text=prompt_text,
                ai_response={},
                execution_time_ms=execution_time,
                status="ERROR",
                error_message=str(e)
            )
        
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        return execution

    async def _build_prompt(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """Build prompt by substituting variables."""
        prompt = template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt

    async def get_execution_history(
        self,
        mapping_id: Optional[uuid.UUID] = None,
        encounter_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> List[MdPromptExecution]:
        """Get prompt execution history."""
        conditions = []
        
        if mapping_id:
            conditions.append(MdPromptExecution.mapping_id == mapping_id)
        
        if encounter_id:
            conditions.append(MdPromptExecution.encounter_id == encounter_id)
        
        query = select(MdPromptExecution)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(MdPromptExecution.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
