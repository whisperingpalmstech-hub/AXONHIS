from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.core.config_service.models import (
    MdConfigItem,
    MdConfigHistory,
    MdConfigGroup,
    MdConfigGroupMapping,
    ConfigScope,
    ConfigDataType
)
from app.core.config_service.schemas import (
    ConfigItemCreate,
    ConfigItemUpdate,
    ConfigGroupCreate,
    ConfigSearchQuery
)


class ConfigService:
    """Service for managing configuration as data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_config(
        self,
        config_data: ConfigItemCreate
    ) -> MdConfigItem:
        """Create a new configuration item."""
        config = MdConfigItem(
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            data_type=config_data.data_type,
            scope=config_data.scope,
            scope_id=config_data.scope_id,
            category=config_data.category,
            description=config_data.description,
            is_sensitive=config_data.is_sensitive,
            is_required=config_data.is_required,
            default_value=config_data.default_value,
            validation_rules=config_data.validation_rules,
            created_by=config_data.created_by,
            effective_from=config_data.effective_from,
            effective_to=config_data.effective_to
        )
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update_config(
        self,
        config_id: uuid.UUID,
        update_data: ConfigItemUpdate,
        change_reason: Optional[str] = None
    ) -> Optional[MdConfigItem]:
        """Update an existing configuration item."""
        query = select(MdConfigItem).where(MdConfigItem.config_id == config_id)
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            return None
        
        # Store old value for history
        old_value = config.config_value
        
        if update_data.config_value is not None:
            config.config_value = update_data.config_value
        if update_data.description is not None:
            config.description = update_data.description
        if update_data.validation_rules is not None:
            config.validation_rules = update_data.validation_rules
        if update_data.updated_by is not None:
            config.updated_by = update_data.updated_by
        if update_data.effective_from is not None:
            config.effective_from = update_data.effective_from
        if update_data.effective_to is not None:
            config.effective_to = update_data.effective_to
        
        config.version += 1
        config.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(config)
        
        # Create history entry
        await self._create_history(
            config_id=config_id,
            config_key=config.config_key,
            old_value=old_value,
            new_value=config.config_value,
            change_reason=change_reason,
            changed_by=update_data.updated_by or config.created_by,
            version=config.version
        )
        
        return config

    async def get_config(
        self,
        config_key: str,
        scope: Optional[ConfigScope] = None,
        scope_id: Optional[uuid.UUID] = None
    ) -> Optional[MdConfigItem]:
        """Get a configuration item by key and scope."""
        conditions = [MdConfigItem.config_key == config_key]
        
        if scope:
            conditions.append(MdConfigItem.scope == scope)
        
        if scope_id:
            conditions.append(MdConfigItem.scope_id == scope_id)
        
        # Check effective dates
        now = datetime.utcnow()
        conditions.append(
            or_(
                MdConfigItem.effective_from.is_(None),
                MdConfigItem.effective_from <= now
            )
        )
        conditions.append(
            or_(
                MdConfigItem.effective_to.is_(None),
                MdConfigItem.effective_to >= now
            )
        )
        
        query = select(MdConfigItem).where(and_(*conditions)).order_by(
            desc(MdConfigItem.scope)  # More specific scopes first
        ).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_config_value(
        self,
        config_key: str,
        scope: Optional[ConfigScope] = None,
        scope_id: Optional[uuid.UUID] = None,
        default: Any = None
    ) -> Any:
        """Get configuration value with fallback to default."""
        config = await self.get_config(config_key, scope, scope_id)
        if config:
            return config.config_value
        return default

    async def search_configs(
        self,
        query: ConfigSearchQuery
    ) -> tuple[List[MdConfigItem], int]:
        """Search configuration items with filters."""
        conditions = []
        
        if query.config_key:
            conditions.append(MdConfigItem.config_key.ilike(f"%{query.config_key}%"))
        
        if query.scope:
            conditions.append(MdConfigItem.scope == query.scope)
        
        if query.scope_id:
            conditions.append(MdConfigItem.scope_id == query.scope_id)
        
        if query.category:
            conditions.append(MdConfigItem.category == query.category)
        
        # Get total count
        count_query = select(func.count(MdConfigItem.config_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        configs_query = select(MdConfigItem)
        if conditions:
            configs_query = configs_query.where(and_(*conditions))
        
        configs_query = configs_query.order_by(desc(MdConfigItem.updated_at)).offset(
            query.offset
        ).limit(query.limit)
        
        configs_result = await self.db.execute(configs_query)
        configs = configs_result.scalars().all()
        
        return list(configs), total_count

    async def get_config_history(
        self,
        config_id: uuid.UUID,
        limit: int = 100
    ) -> List[MdConfigHistory]:
        """Get configuration change history."""
        query = select(MdConfigHistory).where(
            MdConfigHistory.config_id == config_id
        ).order_by(desc(MdConfigHistory.changed_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_config_group(
        self,
        group_data: ConfigGroupCreate
    ) -> MdConfigGroup:
        """Create a new configuration group."""
        group = MdConfigGroup(
            group_name=group_data.group_name,
            group_code=group_data.group_code,
            description=group_data.description,
            category=group_data.category,
            parent_group_id=group_data.parent_group_id,
            sort_order=group_data.sort_order
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_config_groups(
        self,
        category: Optional[str] = None
    ) -> List[MdConfigGroup]:
        """Get configuration groups."""
        conditions = [MdConfigGroup.is_active == True]
        
        if category:
            conditions.append(MdConfigGroup.category == category)
        
        query = select(MdConfigGroup).where(
            and_(*conditions)
        ).order_by(MdConfigGroup.sort_order, MdConfigGroup.group_name)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_config_to_group(
        self,
        group_id: uuid.UUID,
        config_id: uuid.UUID,
        sort_order: int = 0
    ) -> MdConfigGroupMapping:
        """Add a configuration item to a group."""
        mapping = MdConfigGroupMapping(
            group_id=group_id,
            config_id=config_id,
            sort_order=sort_order
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def get_group_configs(
        self,
        group_id: uuid.UUID
    ) -> List[MdConfigItem]:
        """Get all configuration items in a group."""
        query = select(MdConfigItem).join(
            MdConfigGroupMapping,
            MdConfigItem.config_id == MdConfigGroupMapping.config_id
        ).where(
            MdConfigGroupMapping.group_id == group_id
        ).order_by(MdConfigGroupMapping.sort_order)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_config(
        self,
        config_id: uuid.UUID
    ) -> bool:
        """Delete a configuration item."""
        query = select(MdConfigItem).where(MdConfigItem.config_id == config_id)
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            return False
        
        await self.db.delete(config)
        await self.db.commit()
        return True

    async def _create_history(
        self,
        config_id: uuid.UUID,
        config_key: str,
        old_value: Any,
        new_value: Any,
        change_reason: Optional[str],
        changed_by: str,
        version: int
    ):
        """Create a history entry for configuration change."""
        history = MdConfigHistory(
            config_id=config_id,
            config_key=config_key,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            changed_by=changed_by,
            version=version
        )
        self.db.add(history)
        await self.db.commit()

    async def get_configs_by_category(
        self,
        category: str,
        scope: Optional[ConfigScope] = None,
        scope_id: Optional[uuid.UUID] = None
    ) -> List[MdConfigItem]:
        """Get all configurations in a category."""
        conditions = [MdConfigItem.category == category]
        
        if scope:
            conditions.append(MdConfigItem.scope == scope)
        
        if scope_id:
            conditions.append(MdConfigItem.scope_id == scope_id)
        
        query = select(MdConfigItem).where(and_(*conditions)).order_by(MdConfigItem.config_key)
        
        result = await self.db.execute(query)
        return result.scalars().all()
