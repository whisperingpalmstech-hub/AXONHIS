from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.document_template_mappings.schemas import (
    DocumentTemplateMappingCreate,
    DocumentTemplateMappingUpdate,
    DocumentTemplateMappingResponse
)
from app.core.document_template_mappings.services import DocumentTemplateMappingService
from app.database import get_db

router = APIRouter(prefix="/document-templates", tags=["document-templates"])


@router.post("/mappings", response_model=DocumentTemplateMappingResponse)
async def create_template(
    template_data: DocumentTemplateMappingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new document template mapping."""
    service = DocumentTemplateMappingService(db)
    template = await service.create_template(template_data)
    return template


@router.put("/mappings/{mapping_id}", response_model=DocumentTemplateMappingResponse)
async def update_template(
    mapping_id: UUID,
    update_data: DocumentTemplateMappingUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing document template."""
    service = DocumentTemplateMappingService(db)
    template = await service.update_template(mapping_id, update_data)
    if not template:
        raise HTTPException(status_code=404, detail="Document template not found")
    return template


@router.get("/mappings/{mapping_id}", response_model=DocumentTemplateMappingResponse)
async def get_template(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document template."""
    service = DocumentTemplateMappingService(db)
    template = await service.get_template(mapping_id)
    if not template:
        raise HTTPException(status_code=404, detail="Document template not found")
    return template


@router.get("/code/{template_code}", response_model=DocumentTemplateMappingResponse)
async def get_template_by_code(
    template_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a document template by code."""
    service = DocumentTemplateMappingService(db)
    template = await service.get_template_by_code(template_code)
    if not template:
        raise HTTPException(status_code=404, detail="Document template not found")
    return template


@router.get("/type/{document_type}", response_model=List[DocumentTemplateMappingResponse])
async def get_templates_by_type(
    document_type: str,
    specialty_profile_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get document templates by type."""
    service = DocumentTemplateMappingService(db)
    templates = await service.get_templates_by_type(document_type, specialty_profile_id)
    return templates


@router.get("/default/{document_type}", response_model=DocumentTemplateMappingResponse)
async def get_default_template(
    document_type: str,
    specialty_profile_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get the default template for a document type."""
    service = DocumentTemplateMappingService(db)
    template = await service.get_default_template(document_type, specialty_profile_id)
    if not template:
        raise HTTPException(status_code=404, detail="Default template not found")
    return template


@router.get("/mappings", response_model=List[DocumentTemplateMappingResponse])
async def list_templates(
    document_type: str = Query(None),
    specialty_profile_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List document templates with filters."""
    service = DocumentTemplateMappingService(db)
    templates = await service.list_templates(document_type, specialty_profile_id)
    return templates


@router.delete("/mappings/{mapping_id}")
async def delete_template(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document template."""
    service = DocumentTemplateMappingService(db)
    success = await service.delete_template(mapping_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document template not found")
    return {"message": "Document template deleted successfully"}
