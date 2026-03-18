import asyncio
import uuid
from app.database import async_session_maker
from app.core.ot.operating_rooms.models import OperatingRoom, OperatingRoomStatus
from app.core.ot.surgical_procedures.models import SurgicalProcedure

async def seed():
    async with async_session_maker() as session:
        # Add OR if absent
        or1 = OperatingRoom(
            room_code="OR-1",
            room_name="Main Theater",
            department="Cardiology",
            equipment_profile={"monitor": "Philips Intellivue"},
            status=OperatingRoomStatus.AVAILABLE
        )
        session.add(or1)
        
        proc1 = SurgicalProcedure(
            procedure_code="CABG-001",
            procedure_name="Coronary Artery Bypass",
            specialty="Cardiothoracic",
            expected_duration_minutes=240,
            billing_code="CPT-33510",
            required_equipment=["Bypass Machine"]
        )
        session.add(proc1)
        
        await session.commit()
        print(f"Created OR ID: {or1.id}")
        print(f"Created Procedure ID: {proc1.id}")

if __name__ == "__main__":
    asyncio.run(seed())
