import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.ot.surgery_schedule.models import SurgerySchedule, SurgeryStatus
from app.core.ot.anesthesia_records.models import AnesthesiaRecord
from app.core.ot.surgical_procedures.models import SurgicalProcedure
from app.core.billing.billing_entries.models import BillingEntry
from app.core.billing.billing_entries.services import BillingEntryService
from app.core.billing.billing_entries.schemas import BillingEntryCreate


class SurgicalBillingService:
    @staticmethod
    async def generate_surgical_charges(db: AsyncSession, schedule_id: uuid.UUID, user_id: uuid.UUID = None) -> list[BillingEntry]:
        schedule = await db.get(SurgerySchedule, schedule_id)
        if not schedule or schedule.status != SurgeryStatus.COMPLETED:
            return []

        procedure = await db.get(SurgicalProcedure, schedule.procedure_id)
        anesthesia = await db.get(AnesthesiaRecord, schedule_id) # schedule_id is PK/FK for anesthesia

        billing_service = BillingEntryService(db)
        charges = []

        # 1. Procedure Charge
        procedure_charge = BillingEntryCreate(
            encounter_id=schedule.encounter_id,
            patient_id=schedule.patient_id,
            service_id=procedure.id,
            quantity=1,
            unit_price=5000.0
        )
        charges.append(await billing_service.create_entry(procedure_charge, user_id=user_id))

        # 2. Operating Room Usage Charge
        # Note: In a real system, we'd have a specific service_id for OT usage
        room_charge = BillingEntryCreate(
            encounter_id=schedule.encounter_id,
            patient_id=schedule.patient_id,
            service_id=procedure.id, # Using procedure ID as placeholder for service
            quantity=2,
            unit_price=1000.0
        )
        charges.append(await billing_service.create_entry(room_charge, user_id=user_id))

        # 3. Anesthesia Charge
        if anesthesia:
            anesthesia_charge = BillingEntryCreate(
                encounter_id=schedule.encounter_id,
                patient_id=schedule.patient_id,
                service_id=procedure.id, # Using procedure ID as placeholder for service
                quantity=1,
                unit_price=2000.0
            )
            charges.append(await billing_service.create_entry(anesthesia_charge, user_id=user_id))

        # 4. Consumables (Placeholder)
        consumables_charge = BillingEntryCreate(
            encounter_id=schedule.encounter_id,
            patient_id=schedule.patient_id,
            service_id=procedure.id, # Using procedure ID as placeholder for service
            quantity=1,
            unit_price=1500.0
        )
        charges.append(await billing_service.create_entry(consumables_charge, user_id=user_id))

        await db.commit()
        return charges
