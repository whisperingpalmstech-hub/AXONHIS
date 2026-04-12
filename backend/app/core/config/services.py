"""Configuration service – CRUD for runtime settings."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.models import Configuration


class ConfigurationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, key: str) -> str | None:
        result = await self.db.execute(select(Configuration).where(Configuration.key == key))
        config = result.scalar_one_or_none()
        return config.value if config else None

    async def get_all(self, category: str | None = None) -> list[Configuration]:
        stmt = select(Configuration)
        if category:
            stmt = stmt.where(Configuration.category == category)
        result = await self.db.execute(stmt.order_by(Configuration.category, Configuration.key))
        return list(result.scalars().all())

    async def set(self, key: str, value: str, description: str | None = None,
                  category: str = "general", updated_by: uuid.UUID | None = None) -> Configuration:
        result = await self.db.execute(select(Configuration).where(Configuration.key == key))
        config = result.scalar_one_or_none()
        if config:
            config.value = value
            if description:
                config.description = description
            config.updated_by = updated_by
        else:
            config = Configuration(
                key=key, value=value, description=description,
                category=category, updated_by=updated_by,
            )
            self.db.add(config)
        await self.db.flush()
        return config

    async def delete(self, key: str) -> bool:
        result = await self.db.execute(select(Configuration).where(Configuration.key == key))
        config = result.scalar_one_or_none()
        if config:
            await self.db.delete(config)
            await self.db.flush()
            return True
        return False
