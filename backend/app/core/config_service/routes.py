from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config_service.schemas import (
    ConfigItemCreate,
    ConfigItemUpdate,
    ConfigItemResponse,
    ConfigHistoryResponse,
    ConfigGroupCreate,
    ConfigGroupResponse,
    ConfigSearchQuery,
    ConfigSearchResponse
)
from app.core.config_service.services import ConfigService
from app.database import get_db

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/items", response_model=ConfigItemResponse)
async def create_config(
    config_data: ConfigItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new configuration item."""
    service = ConfigService(db)
    config = await service.create_config(config_data)
    return config


@router.put("/items/{config_id}", response_model=ConfigItemResponse)
async def update_config(
    config_id: UUID,
    update_data: ConfigItemUpdate,
    change_reason: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing configuration item."""
    service = ConfigService(db)
    config = await service.update_config(config_id, update_data, change_reason)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.get("/items/{config_key}", response_model=ConfigItemResponse)
async def get_config(
    config_key: str,
    scope: str = Query(None),
    scope_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get a configuration item by key and scope."""
    service = ConfigService(db)
    config = await service.get_config(config_key, scope, scope_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.get("/items/{config_key}/value")
async def get_config_value(
    config_key: str,
    scope: str = Query(None),
    scope_id: UUID = Query(None),
    default: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get configuration value with fallback to default."""
    service = ConfigService(db)
    value = await service.get_config_value(config_key, scope, scope_id, default)
    return {"config_key": config_key, "value": value}


@router.post("/items/search", response_model=ConfigSearchResponse)
async def search_configs(
    query: ConfigSearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """Search configuration items with filters."""
    service = ConfigService(db)
    configs, total_count = await service.search_configs(query)
    has_more = (query.offset + query.limit) < total_count
    return ConfigSearchResponse(
        configs=configs,
        total_count=total_count,
        has_more=has_more
    )


@router.get("/items/{config_id}/history", response_model=List[ConfigHistoryResponse])
async def get_config_history(
    config_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get configuration change history."""
    service = ConfigService(db)
    history = await service.get_config_history(config_id, limit)
    return history


@router.delete("/items/{config_id}")
async def delete_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a configuration item."""
    service = ConfigService(db)
    success = await service.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Configuration deleted successfully"}


@router.post("/groups", response_model=ConfigGroupResponse)
async def create_config_group(
    group_data: ConfigGroupCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new configuration group."""
    service = ConfigService(db)
    group = await service.create_config_group(group_data)
    return group


@router.get("/groups", response_model=List[ConfigGroupResponse])
async def get_config_groups(
    category: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get configuration groups."""
    service = ConfigService(db)
    groups = await service.get_config_groups(category)
    return groups


@router.post("/groups/{group_id}/configs/{config_id}")
async def add_config_to_group(
    group_id: UUID,
    config_id: UUID,
    sort_order: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Add a configuration item to a group."""
    service = ConfigService(db)
    mapping = await service.add_config_to_group(group_id, config_id, sort_order)
    return {"message": "Configuration added to group"}


@router.get("/groups/{group_id}/configs", response_model=List[ConfigItemResponse])
async def get_group_configs(
    group_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all configuration items in a group."""
    service = ConfigService(db)
    configs = await service.get_group_configs(group_id)
    return configs


@router.get("/category/{category}", response_model=List[ConfigItemResponse])
async def get_configs_by_category(
    category: str,
    scope: str = Query(None),
    scope_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all configurations in a category."""
    service = ConfigService(db)
    configs = await service.get_configs_by_category(category, scope, scope_id)
    return configs
