from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.core.device_adapter.models import (
    MdDeviceAdapter,
    MdDeviceData,
    MdAdapterCommand,
    MdAdapterLog,
    AdapterStatus
)
from app.core.device_adapter.schemas import (
    DeviceAdapterCreate,
    DeviceAdapterUpdate,
    DeviceDataCreate,
    AdapterCommandCreate
)


class DeviceAdapterService:
    """Service for managing device adapters and device data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_adapter(
        self,
        adapter_data: DeviceAdapterCreate
    ) -> MdDeviceAdapter:
        """Create a new device adapter."""
        adapter = MdDeviceAdapter(
            adapter_name=adapter_data.adapter_name,
            adapter_type=adapter_data.adapter_type,
            protocol=adapter_data.protocol,
            connection_config=adapter_data.connection_config,
            device_id=adapter_data.device_id,
            facility_id=adapter_data.facility_id,
            data_mapping=adapter_data.data_mapping,
            transformation_rules=adapter_data.transformation_rules,
            polling_interval_seconds=adapter_data.polling_interval_seconds,
            auto_reconnect=adapter_data.auto_reconnect,
            created_by=adapter_data.created_by
        )
        self.db.add(adapter)
        await self.db.commit()
        await self.db.refresh(adapter)
        
        # Log creation
        await self._log_adapter_activity(
            adapter_id=adapter.adapter_id,
            log_level="INFO",
            message=f"Adapter created: {adapter.adapter_name}"
        )
        
        return adapter

    async def update_adapter(
        self,
        adapter_id: uuid.UUID,
        update_data: DeviceAdapterUpdate
    ) -> Optional[MdDeviceAdapter]:
        """Update an existing device adapter."""
        query = select(MdDeviceAdapter).where(MdDeviceAdapter.adapter_id == adapter_id)
        result = await self.db.execute(query)
        adapter = result.scalar_one_or_none()
        
        if not adapter:
            return None
        
        if update_data.adapter_name is not None:
            adapter.adapter_name = update_data.adapter_name
        if update_data.connection_config is not None:
            adapter.connection_config = update_data.connection_config
        if update_data.data_mapping is not None:
            adapter.data_mapping = update_data.data_mapping
        if update_data.transformation_rules is not None:
            adapter.transformation_rules = update_data.transformation_rules
        if update_data.polling_interval_seconds is not None:
            adapter.polling_interval_seconds = update_data.polling_interval_seconds
        if update_data.auto_reconnect is not None:
            adapter.auto_reconnect = update_data.auto_reconnect
        if update_data.status is not None:
            adapter.status = update_data.status
        
        adapter.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(adapter)
        
        await self._log_adapter_activity(
            adapter_id=adapter.adapter_id,
            log_level="INFO",
            message=f"Adapter updated: {adapter.adapter_name}"
        )
        
        return adapter

    async def get_adapter(
        self,
        adapter_id: uuid.UUID
    ) -> Optional[MdDeviceAdapter]:
        """Get a specific device adapter."""
        query = select(MdDeviceAdapter).where(MdDeviceAdapter.adapter_id == adapter_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_adapters(
        self,
        adapter_type: Optional[str] = None,
        status: Optional[AdapterStatus] = None,
        facility_id: Optional[uuid.UUID] = None
    ) -> List[MdDeviceAdapter]:
        """List device adapters with filters."""
        conditions = []
        
        if adapter_type:
            conditions.append(MdDeviceAdapter.adapter_type == adapter_type)
        
        if status:
            conditions.append(MdDeviceAdapter.status == status)
        
        if facility_id:
            conditions.append(MdDeviceAdapter.facility_id == facility_id)
        
        query = select(MdDeviceAdapter)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(MdDeviceAdapter.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def ingest_device_data(
        self,
        data: DeviceDataCreate
    ) -> MdDeviceData:
        """Ingest raw data from a device."""
        adapter = await self.get_adapter(data.adapter_id)
        if not adapter:
            raise ValueError("Adapter not found")
        
        # Process data using mapping and transformation rules
        processed_data = await self._process_data(
            raw_data=data.raw_data,
            data_mapping=adapter.data_mapping,
            transformation_rules=adapter.transformation_rules
        )
        
        device_data = MdDeviceData(
            adapter_id=data.adapter_id,
            encounter_id=data.encounter_id,
            patient_id=data.patient_id,
            raw_data=data.raw_data,
            processed_data=processed_data,
            observation_type=data.observation_type,
            data_quality_score=self._calculate_data_quality(data.raw_data),
            status="PROCESSED"
        )
        
        self.db.add(device_data)
        await self.db.commit()
        await self.db.refresh(device_data)
        
        # Update adapter heartbeat
        adapter.last_heartbeat = datetime.utcnow()
        adapter.status = AdapterStatus.ACTIVE
        adapter.last_error = None
        await self.db.commit()
        
        return device_data

    async def _process_data(
        self,
        raw_data: Dict[str, Any],
        data_mapping: Dict[str, Any],
        transformation_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process raw data using mapping and transformation rules."""
        processed = {}
        
        # Apply field mappings
        for system_field, device_field in data_mapping.items():
            if device_field in raw_data:
                processed[system_field] = raw_data[device_field]
        
        # Apply transformation rules
        for rule in transformation_rules:
            rule_type = rule.get("type")
            if rule_type == "scale":
                field = rule.get("field")
                factor = rule.get("factor", 1.0)
                if field in processed:
                    processed[field] = processed[field] * factor
            elif rule_type == "offset":
                field = rule.get("field")
                offset = rule.get("offset", 0)
                if field in processed:
                    processed[field] = processed[field] + offset
            elif rule_type == "format":
                field = rule.get("field")
                format_type = rule.get("format")
                if field in processed:
                    if format_type == "string":
                        processed[field] = str(processed[field])
                    elif format_type == "int":
                        processed[field] = int(processed[field])
                    elif format_type == "float":
                        processed[field] = float(processed[field])
        
        return processed

    def _calculate_data_quality(self, raw_data: Dict[str, Any]) -> float:
        """Calculate data quality score (0-100)."""
        if not raw_data:
            return 0.0
        
        # Simple heuristic: check for null values and reasonable ranges
        total_fields = len(raw_data)
        valid_fields = 0
        
        for value in raw_data.values():
            if value is not None and value != "":
                valid_fields += 1
        
        return (valid_fields / total_fields) * 100 if total_fields > 0 else 0.0

    async def send_command(
        self,
        command_data: AdapterCommandCreate
    ) -> MdAdapterCommand:
        """Send a command to a device adapter."""
        adapter = await self.get_adapter(command_data.adapter_id)
        if not adapter:
            raise ValueError("Adapter not found")
        
        command = MdAdapterCommand(
            adapter_id=command_data.adapter_id,
            command_type=command_data.command_type,
            command_payload=command_data.command_payload,
            status="PENDING"
        )
        self.db.add(command)
        await self.db.commit()
        await self.db.refresh(command)
        
        # In a real implementation, this would send the command to the device
        # For now, we'll simulate sending
        command.status = "SENT"
        command.sent_at = datetime.utcnow()
        await self.db.commit()
        
        await self._log_adapter_activity(
            adapter_id=adapter.adapter_id,
            log_level="INFO",
            message=f"Command sent: {command_data.command_type}"
        )
        
        return command

    async def get_adapter_health(
        self,
        adapter_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get health status of an adapter."""
        adapter = await self.get_adapter(adapter_id)
        if not adapter:
            return {"error": "Adapter not found"}
        
        # Count data points in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        data_query = select(func.count(MdDeviceData.data_id)).where(
            and_(
                MdDeviceData.adapter_id == adapter_id,
                MdDeviceData.received_at >= one_hour_ago
            )
        )
        data_result = await self.db.execute(data_query)
        data_points = data_result.scalar() or 0
        
        # Count errors in last hour
        error_query = select(func.count(MdAdapterLog.log_id)).where(
            and_(
                MdAdapterLog.adapter_id == adapter_id,
                MdAdapterLog.log_level == "ERROR",
                MdAdapterLog.created_at >= one_hour_ago
            )
        )
        error_result = await self.db.execute(error_query)
        error_count = error_result.scalar() or 0
        
        is_connected = (
            adapter.status == AdapterStatus.ACTIVE and
            adapter.last_heartbeat and
            (datetime.utcnow() - adapter.last_heartbeat).total_seconds() < 300
        )
        
        return {
            "adapter_id": str(adapter.adapter_id),
            "adapter_name": adapter.adapter_name,
            "status": adapter.status,
            "last_heartbeat": adapter.last_heartbeat.isoformat() if adapter.last_heartbeat else None,
            "is_connected": is_connected,
            "data_points_last_hour": data_points,
            "error_count_last_hour": error_count
        }

    async def _log_adapter_activity(
        self,
        adapter_id: uuid.UUID,
        log_level: str,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """Log adapter activity."""
        log = MdAdapterLog(
            adapter_id=adapter_id,
            log_level=log_level,
            message=message,
            metadata=metadata or {}
        )
        self.db.add(log)
        await self.db.commit()

    async def get_device_data(
        self,
        adapter_id: uuid.UUID,
        patient_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MdDeviceData]:
        """Get device data with filters."""
        conditions = [MdDeviceData.adapter_id == adapter_id]
        
        if patient_id:
            conditions.append(MdDeviceData.patient_id == patient_id)
        
        if start_date:
            conditions.append(MdDeviceData.received_at >= start_date)
        
        if end_date:
            conditions.append(MdDeviceData.received_at <= end_date)
        
        query = select(MdDeviceData).where(
            and_(*conditions)
        ).order_by(desc(MdDeviceData.received_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
