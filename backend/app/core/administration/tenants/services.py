import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from .models import OrganizationEntity, FacilitySite
from .schemas import OrgCreate, SiteCreate

class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_organizations(self, org_id: uuid.UUID = None):
        q = select(OrganizationEntity).options(selectinload(OrganizationEntity.sites))
        if org_id:
            q = q.where(OrganizationEntity.id == org_id)
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def create_organization(self, data: OrgCreate) -> OrganizationEntity:
        org = OrganizationEntity(**data.model_dump(exclude={"admin_password"}))
        self.db.add(org)
        try:
            await self.db.flush()
        except BaseException as e:
            raise HTTPException(400, "Org Code or Name already exists.")
        
        # Auto-create HQ Site by default to instantly configure the master
        hq_site = FacilitySite(
            org_id=org.id,
            name=f"{org.name} - Headquarters",
            site_code=f"{org.org_code}-HQ",
            site_settings={"voice_enabled": True}
        )
        self.db.add(hq_site)

        # Automatically Provision a Super Admin for this Tenant
        from app.core.auth.models import User
        from app.core.auth.services import hash_password
        
        tenant_admin_email = f"admin@{org.org_code.lower()}.com"
        req_password = data.admin_password or "Admin@123"
        admin_user = User(
            email=tenant_admin_email,
            password_hash=hash_password(req_password),
            first_name=org.name,
            last_name="SuperAdmin",
            phone="0000000000",
            org_id=org.id
        )
        self.db.add(admin_user)
        await self.db.flush()
        
        return await self.get_org(org.id)

    async def get_org(self, org_id: uuid.UUID):
        q = select(OrganizationEntity).options(selectinload(OrganizationEntity.sites)).where(OrganizationEntity.id == org_id)
        org = (await self.db.execute(q)).scalar_one_or_none()
        if not org:
            raise HTTPException(404, "Organization not found")
        return org

    async def add_site(self, org_id: uuid.UUID, data: SiteCreate) -> FacilitySite:
        # Validate org exists
        await self.get_org(org_id)
        
        site = FacilitySite(org_id=org_id, **data.model_dump())
        self.db.add(site)
        try:
            await self.db.flush()
        except:
            raise HTTPException(400, "Site Code already exists.")
        return site

    async def toggle_voice_ai(self, org_id: uuid.UUID, enable: bool):
        org = await self.get_org(org_id)
        if not org.global_settings:
            org.global_settings = {}
        # Avoid direct dict mutation tracking issues in SQLAlchemy JSONB by replacing dict
        new_settings = dict(org.global_settings)
        new_settings["voice_ai_enabled"] = enable
        org.global_settings = new_settings
        await self.db.flush()
        return org

    async def change_language(self, org_id: uuid.UUID, lang: str):
        org = await self.get_org(org_id)
        org.default_language = lang
        await self.db.flush()
        return org
