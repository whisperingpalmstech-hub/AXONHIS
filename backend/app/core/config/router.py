"""Configuration router – manage runtime settings."""
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.audit.services import AuditService
from app.core.config.services import ConfigurationService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/config", tags=["config"])


class ConfigOut(BaseModel):
    key: str
    value: str
    description: str | None
    category: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfigSet(BaseModel):
    key: str
    value: str
    description: str | None = None
    category: str = "general"


@router.get("", response_model=list[ConfigOut])
async def list_configs(
    db: DBSession, _: CurrentUser, category: str | None = Query(None)
) -> list[ConfigOut]:
    configs = await ConfigurationService(db).get_all(category=category)
    return [ConfigOut.model_validate(c) for c in configs]


@router.get("/{key}", response_model=ConfigOut)
async def get_config(key: str, db: DBSession, _: CurrentUser) -> ConfigOut:
    service = ConfigurationService(db)
    configs = await service.get_all()
    for c in configs:
        if c.key == key:
            return ConfigOut.model_validate(c)
    raise HTTPException(status_code=404, detail="Configuration key not found")


@router.put("", response_model=ConfigOut)
async def set_config(data: ConfigSet, db: DBSession, user: CurrentUser) -> ConfigOut:
    service = ConfigurationService(db)
    old_value = await service.get(data.key)
    config = await service.set(
        key=data.key, value=data.value, description=data.description,
        category=data.category, updated_by=user.id,
    )
    await AuditService(db).log(
        user_id=user.id, action="config_changed", entity_type="configuration",
        entity_id=data.key, old_value={"value": old_value}, new_value={"value": data.value},
    )
    return ConfigOut.model_validate(config)


@router.delete("/{key}", status_code=204)
async def delete_config(key: str, db: DBSession, user: CurrentUser) -> None:
    success = await ConfigurationService(db).delete(key)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration key not found")
