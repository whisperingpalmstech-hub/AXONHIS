from datetime import datetime
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.core.document_template_mappings.models import MdDocumentTemplateMapping
from app.core.document_template_mappings.schemas import (
    DocumentTemplateMappingCreate,
    DocumentTemplateMappingUpdate
)


class DocumentTemplateMappingService:
    """Service for managing document template mappings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(
        self,
        template_data: DocumentTemplateMappingCreate
    ) -> MdDocumentTemplateMapping:
        """Create a new document template mapping."""
        template = MdDocumentTemplateMapping(
            template_name=template_data.template_name,
            template_code=template_data.template_code,
            document_type=template_data.document_type,
            specialty_profile_id=template_data.specialty_profile_id,
            template_content=template_data.template_content,
            template_variables=template_data.template_variables,
            output_format=template_data.output_format,
            metadata=template_data.metadata,
            is_default=template_data.is_default,
            created_by=template_data.created_by
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self,
        mapping_id: uuid.UUID,
        update_data: DocumentTemplateMappingUpdate
    ) -> Optional[MdDocumentTemplateMapping]:
        """Update an existing document template."""
        query = select(MdDocumentTemplateMapping).where(
            MdDocumentTemplateMapping.mapping_id == mapping_id
        )
        result = await self.db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        if update_data.template_name is not None:
            template.template_name = update_data.template_name
        if update_data.template_content is not None:
            template.template_content = update_data.template_content
        if update_data.template_variables is not None:
            template.template_variables = update_data.template_variables
        if update_data.output_format is not None:
            template.output_format = update_data.output_format
        if update_data.metadata is not None:
            template.metadata = update_data.metadata
        if update_data.is_default is not None:
            template.is_default = update_data.is_default
        if update_data.is_active is not None:
            template.is_active = update_data.is_active
        
        template.version += 1
        template.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_template(
        self,
        mapping_id: uuid.UUID
    ) -> Optional[MdDocumentTemplateMapping]:
        """Get a specific document template."""
        query = select(MdDocumentTemplateMapping).where(
            MdDocumentTemplateMapping.mapping_id == mapping_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_template_by_code(
        self,
        template_code: str
    ) -> Optional[MdDocumentTemplateMapping]:
        """Get a document template by code."""
        query = select(MdDocumentTemplateMapping).where(
            and_(
                MdDocumentTemplateMapping.template_code == template_code,
                MdDocumentTemplateMapping.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_templates_by_type(
        self,
        document_type: str,
        specialty_profile_id: Optional[uuid.UUID] = None
    ) -> List[MdDocumentTemplateMapping]:
        """Get document templates by type."""
        conditions = [
            MdDocumentTemplateMapping.document_type == document_type,
            MdDocumentTemplateMapping.is_active == True
        ]
        
        if specialty_profile_id:
            conditions.append(MdDocumentTemplateMapping.specialty_profile_id == specialty_profile_id)
        
        query = select(MdDocumentTemplateMapping).where(
            and_(*conditions)
        ).order_by(desc(MdDocumentTemplateMapping.is_default), MdDocumentTemplateMapping.template_name)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_default_template(
        self,
        document_type: str,
        specialty_profile_id: Optional[uuid.UUID] = None
    ) -> Optional[MdDocumentTemplateMapping]:
        """Get the default template for a document type."""
        conditions = [
            MdDocumentTemplateMapping.document_type == document_type,
            MdDocumentTemplateMapping.is_default == True,
            MdDocumentTemplateMapping.is_active == True
        ]
        
        if specialty_profile_id:
            conditions.append(MdDocumentTemplateMapping.specialty_profile_id == specialty_profile_id)
        
        query = select(MdDocumentTemplateMapping).where(and_(*conditions)).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        document_type: Optional[str] = None,
        specialty_profile_id: Optional[uuid.UUID] = None
    ) -> List[MdDocumentTemplateMapping]:
        """List document templates with filters."""
        conditions = [MdDocumentTemplateMapping.is_active == True]
        
        if document_type:
            conditions.append(MdDocumentTemplateMapping.document_type == document_type)
        
        if specialty_profile_id:
            conditions.append(MdDocumentTemplateMapping.specialty_profile_id == specialty_profile_id)
        
        query = select(MdDocumentTemplateMapping)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(MdDocumentTemplateMapping.document_type, MdDocumentTemplateMapping.template_name)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_template(
        self,
        mapping_id: uuid.UUID
    ) -> bool:
        """Delete a document template."""
        query = select(MdDocumentTemplateMapping).where(
            MdDocumentTemplateMapping.mapping_id == mapping_id
        )
        result = await self.db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            return False
        
        await self.db.delete(template)
        await self.db.commit()
        return True
