from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.device_adapter.schemas import (
    DeviceAdapterCreate,
    DeviceAdapterUpdate,
    DeviceAdapterResponse,
    DeviceDataCreate,
    DeviceDataResponse,
    AdapterCommandCreate,
    AdapterCommandResponse,
    AdapterHealthCheck
)
from app.core.device_adapter.services import DeviceAdapterService
from app.database import get_db

router = APIRouter(prefix="/device-adapter", tags=["device-adapter"])


@router.post("/adapters", response_model=DeviceAdapterResponse)
async def create_adapter(
    adapter_data: DeviceAdapterCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device adapter."""
    service = DeviceAdapterService(db)
    adapter = await service.create_adapter(adapter_data)
    return adapter


@router.put("/adapters/{adapter_id}", response_model=DeviceAdapterResponse)
async def update_adapter(
    adapter_id: UUID,
    update_data: DeviceAdapterUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing device adapter."""
    service = DeviceAdapterService(db)
    adapter = await service.update_adapter(adapter_id, update_data)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found")
    return adapter


@router.get("/adapters/{adapter_id}", response_model=DeviceAdapterResponse)
async def get_adapter(
    adapter_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific device adapter."""
    service = DeviceAdapterService(db)
    adapter = await service.get_adapter(adapter_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Adapter not found")
    return adapter


@router.get("/adapters", response_model=List[DeviceAdapterResponse])
async def list_adapters(
    adapter_type: str = Query(None),
    status: str = Query(None),
    facility_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List device adapters with filters."""
    service = DeviceAdapterService(db)
    adapters = await service.list_adapters(
        adapter_type=adapter_type,
        status=status,
        facility_id=facility_id
    )
    return adapters


@router.post("/data", response_model=DeviceDataResponse)
async def ingest_device_data(
    data: DeviceDataCreate,
    db: AsyncSession = Depends(get_db)
):
    """Ingest raw data from a device."""
    service = DeviceAdapterService(db)
    device_data = await service.ingest_device_data(data)
    return device_data


@router.get("/adapters/{adapter_id}/data", response_model=List[DeviceDataResponse])
async def get_device_data(
    adapter_id: UUID,
    patient_id: UUID = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get device data with filters."""
    from datetime import datetime
    
    service = DeviceAdapterService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    data = await service.get_device_data(
        adapter_id=adapter_id,
        patient_id=patient_id,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit
    )
    return data


@router.post("/adapters/{adapter_id}/commands", response_model=AdapterCommandResponse)
async def send_command(
    adapter_id: UUID,
    command_data: AdapterCommandCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a command to a device adapter."""
    service = DeviceAdapterService(db)
    command_data.adapter_id = adapter_id
    command = await service.send_command(command_data)
    return command


@router.get("/adapters/{adapter_id}/health", response_model=AdapterHealthCheck)
async def get_adapter_health(
    adapter_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get health status of an adapter."""
    service = DeviceAdapterService(db)
    health = await service.get_adapter_health(adapter_id)
    if "error" in health:
        raise HTTPException(status_code=404, detail=health["error"])
    return health
