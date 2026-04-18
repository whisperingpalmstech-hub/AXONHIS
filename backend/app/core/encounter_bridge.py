"""
Encounter Bridge Service — Central Integration Hub

This service ensures all modules are connected through encounters.
When actions happen in one module, they automatically propagate to related modules.
"""
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class EncounterBridgeService:
    """
    Central service that bridges all modules through encounter_id.
    
    Flow:
    OPD Visit → Encounter → Triage → Doctor Desk → [Pharmacy, LIS, Billing]
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ─── 1. Create Encounter when OPD visit is created ─────────────────────
    async def create_encounter_for_visit(
        self, patient_id: uuid.UUID, org_id: uuid.UUID,
        doctor_id: Optional[uuid.UUID] = None,
        chief_complaint: Optional[str] = None, encounter_type: str = "OPD"
    ) -> "Encounter":
        """Creates a real Encounter record linked to a patient visit."""
        from app.core.encounters.models import Encounter
        
        # Ensure we have a valid doctor_id or a system default if allowed
        # But per schema it is nullable=False now. 
        # If doctor_id is None, we use a fallback if possible or let it fail 
        enc = Encounter(
            patient_id=patient_id,
            encounter_type=encounter_type,
            status="ACTIVE",
            doctor_id=doctor_id, # Can be None now!
            encounter_uuid=f"ENC-{str(uuid.uuid4())[:8].upper()}",
            department="OPD",
            org_id=org_id
        )
        self.db.add(enc)
        await self.db.flush()
        logger.info(f"[BRIDGE] Created Encounter {enc.id} for patient {patient_id}")
        return enc
    
    # ─── 2. Add patient to Doctor Worklist after Triage ────────────────────
    async def add_to_doctor_worklist(
        self, patient_id: uuid.UUID, doctor_id: uuid.UUID,
        visit_id: uuid.UUID, encounter_id: uuid.UUID,
        org_id: uuid.UUID,
        chief_complaint: str = ""
    ):
        """After triage completion, auto-add patient to doctor's worklist."""
        from app.core.doctor_desk.models import DoctorWorklist, ConsultStatus
        
        # Check if already in worklist
        existing = await self.db.execute(
            select(DoctorWorklist).where(and_(
                DoctorWorklist.patient_id == patient_id,
                DoctorWorklist.visit_id == visit_id
            ))
        )
        if existing.scalar_one_or_none():
            logger.info(f"[BRIDGE] Patient {patient_id} already in doctor worklist")
            return
        
        wl = DoctorWorklist(
            doctor_id=doctor_id,
            patient_id=patient_id,
            visit_id=visit_id,
            chief_complaint=chief_complaint,
            status=ConsultStatus.waiting,
            org_id=org_id
        )
        self.db.add(wl)
        await self.db.flush()
        logger.info(f"[BRIDGE] Added patient {patient_id} to doctor {doctor_id} worklist")
    
    # ─── 3. Push Doctor Prescription to Pharmacy Worklist ──────────────────
    async def push_prescription_to_pharmacy(
        self, patient_id: uuid.UUID, visit_id: uuid.UUID,
        medication_name: str, dosage: str, frequency: str, duration: str,
        org_id: uuid.UUID,
        doctor_id: Optional[uuid.UUID] = None
    ):
        """When doctor prescribes medication, auto-create pharmacy worklist entry.
        Corrected field names to match the actual Pharmacy sales worklist models."""
        from app.core.pharmacy.sales_worklist.models import (
            PharmacySalesWorklist, PharmacyPrescription
        )
        from app.core.patients.patients.models import Patient
        
        # 1. Fetch Patient Info for the pharmacy dashboard
        pat_res = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        patient = pat_res.scalars().first()
        p_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        p_uhid = patient.patient_uuid[:8].upper() if patient else "N/A"

        # 2. Find Or Create Active Pharmacy Worklist for this patient/visit
        wl_res = await self.db.execute(
            select(PharmacySalesWorklist).where(
                and_(
                    PharmacySalesWorklist.patient_id == patient_id,
                    PharmacySalesWorklist.status.in_(["Pending", "In Progress"])
                )
            ).order_by(PharmacySalesWorklist.created_at.desc())
        )
        wl = wl_res.scalars().first()
        
        if not wl:
            # We use the UHID here so the pharmacist can actually identify them
            wl = PharmacySalesWorklist(
                id=uuid.uuid4(),
                patient_id=patient_id,
                patient_name=p_name,
                uhid=p_uhid,
                visit_id=visit_id,
                status="Pending",
                prescription_id=uuid.uuid4(), # Unified identifier
                doctor_name="Doctor Desk (Auto-Bridge)",
                org_id=org_id
            )
            self.db.add(wl)
            await self.db.flush()
        
        # 3. Add prescription item (Matching the actual model schema)
        rx_item = PharmacyPrescription(
            id=uuid.uuid4(),
            worklist_id=wl.id,
            medication_name=medication_name,
            dosage_instructions=f"{dosage} - {frequency} ({duration})",
            quantity_prescribed=1, # Default placeholder for OPD
            doctor_notes="Automated routing from Doctor Desk consultation",
            org_id=org_id
        )
        self.db.add(rx_item)
        await self.db.flush()
        
        logger.info(f"[BRIDGE] Pushed Prescription ({medication_name}) to Pharmacy for {p_name}")
        return wl.id
    
    # ─── 4. Push Doctor Diagnostic Order to LIS ────────────────────────────
    async def push_diagnostic_to_lis(
        self, patient_id: uuid.UUID, encounter_id: uuid.UUID,
        test_name: str, doctor_id: uuid.UUID,
        org_id: uuid.UUID,
        priority: str = "routine", sample_type: str = "BLOOD"
    ):
        """When doctor orders diagnostics, auto-create LIS test order and phlebotomy entry."""
        from app.core.lab.test_order_engine.models import LISTestOrder, LISTestOrderItem
        from app.core.lab.phlebotomy_engine.models import PhlebotomyWorklist
        
        order_number = f"LAB-ORD-{datetime.utcnow().strftime('%Y')}-{str(uuid.uuid4().int)[:6]}"
        
        # 1. Create the Main Order
        order = LISTestOrder(
            order_number=order_number,
            patient_id=patient_id,
            ordering_doctor=str(doctor_id),
            encounter_id=encounter_id,
            order_source="DOCTOR_DESK",
            department_source="DOCTOR_DESK",
            priority=priority.upper() if priority else "ROUTINE",
            status="ORDERED",
            org_id=org_id
        )
        self.db.add(order)
        await self.db.flush()
        
        # 2. Create the Order Item
        item = LISTestOrderItem(
            order_id=order.id,
            test_code=test_name.upper().replace(' ', '_')[:50],
            test_name=test_name,
            sample_type=sample_type,
            priority=priority.upper() if priority else "ROUTINE",
            status="ORDERED",
            org_id=org_id
        )
        self.db.add(item)
        await self.db.flush()

        # 3. Create the Phlebotomy Worklist Entry (This makes it visible in the Phlebotomy DASHBOARD)
        # Fetch actual patient details for the dashboard
        from app.core.patients.patients.models import Patient
        patient_res = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        patient_obj = patient_res.scalars().first()
        
        patient_name = f"{patient_obj.first_name} {patient_obj.last_name}" if patient_obj else "Unknown"
        patient_uhid = patient_obj.patient_uuid[:8] if patient_obj else "N/A" # Use prefix as UHID if not explicit

        wl_item = PhlebotomyWorklist(
            id=uuid.uuid4(),
            order_id=order.id,
            order_item_id=item.id,
            order_number=order_number,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_uhid=patient_uhid,
            visit_id=encounter_id,
            test_code=item.test_code,
            test_name=test_name,
            sample_type=sample_type.upper(),
            priority=priority.upper() if priority else "ROUTINE",
            status="PENDING_COLLECTION",
            collection_location="OPD",
            org_id=org_id
        )
        self.db.add(wl_item)
        await self.db.flush()
        
        logger.info(f"[BRIDGE] Created Lab Order & Phlebotomy entry for {test_name} (Patient: {patient_name})")
        return order
    
    # ─── 5. Auto-capture billing charges from encounter ────────────────────
    async def get_encounter_charges(self, patient_id: uuid.UUID, encounter_id: Optional[uuid.UUID] = None):
        """
        Aggregate all charges from an encounter for billing.
        Pulls from: OPD consultation, Lab orders, Pharmacy prescriptions
        Deduplicates by service_name and applies Master Tariff prices.
        """
        from app.core.rcm_billing.models import BillingTariff
        from sqlalchemy import select, or_

        seen_services = set()
        charges = []
        
        # Pre-fetch all active tariffs once to avoid N+1 queries
        tariff_res = await self.db.execute(select(BillingTariff).where(BillingTariff.is_active == True))
        tariffs = {t.service_name.lower().strip(): t.price for t in tariff_res.scalars().all()}

        def _add_charge(service_name: str, department: str, quantity: int = 1):
            """Add charge with tariff lookup and dedup."""
            key = service_name.lower().strip()
            if key not in seen_services:
                seen_services.add(key)
                
                # Dynamic Price Lookup: Check Tariff first
                price = tariffs.get(key, 0.0) # Default to 0 if not in tariff
                
                # Special cases for prescriptions (usually have dynamic prices)
                if department == "Pharmacy" and price == 0:
                    price = 100.0 # Default pharmacy placeholder if NOT in tariff
                elif department == "Diagnostics" and price == 0:
                    price = 800.0 # Default lab placeholder if NOT in tariff
                elif department == "OPD" and price == 0:
                    price = 500.0 # Default OPD placeholder if NOT in tariff

                charges.append({
                    "service_name": service_name,
                    "department": department,
                    "quantity": quantity,
                    "base_rate": price,
                    "total_cost": price * quantity,
                    "is_auto_billed": True,
                })
        
        # 1. Consultation charge
        _add_charge("OPD Consultation Fee", "OPD")
        
        # 2. Lab order charges (from LIS)
        try:
            from app.core.lab.test_order_engine.models import LISTestOrder, LISTestOrderItem
            lab_q = select(LISTestOrder).where(LISTestOrder.patient_id == patient_id)
            if encounter_id:
                lab_q = lab_q.where(LISTestOrder.encounter_id == encounter_id)
            lab_orders = (await self.db.execute(lab_q)).scalars().all()
            
            for order in lab_orders:
                items_q = select(LISTestOrderItem).where(LISTestOrderItem.order_id == order.id)
                items = (await self.db.execute(items_q)).scalars().all()
                for item in items:
                    _add_charge(item.test_name, "Diagnostics")
        except Exception as e:
            logger.warning(f"[BRIDGE] Could not fetch lab charges: {e}")
        
        # 3. Pharmacy/Prescription charges from doctor desk
        try:
            from app.core.doctor_desk.models import DoctorPrescription, DoctorWorklist
            wl_q = select(DoctorWorklist.visit_id).where(DoctorWorklist.patient_id == patient_id)
            visit_ids = list((await self.db.execute(wl_q)).scalars().all())
            
            if visit_ids:
                rx_q = select(DoctorPrescription).where(DoctorPrescription.visit_id.in_(visit_ids))
                prescriptions = (await self.db.execute(rx_q)).scalars().all()
                
                for rx in prescriptions:
                    _add_charge(f"Rx: {rx.medicine_name}", "Pharmacy")
        except Exception as e:
            logger.warning(f"[BRIDGE] Could not fetch pharmacy charges: {e}")
        
        # 4. Diagnostic orders from doctor desk (deduped with LIS items above)
        try:
            from app.core.doctor_desk.models import DoctorDiagnosticOrder, DoctorWorklist
            wl_q = select(DoctorWorklist.visit_id).where(DoctorWorklist.patient_id == patient_id)
            visit_ids = list((await self.db.execute(wl_q)).scalars().all())
            
            if visit_ids:
                diag_q = select(DoctorDiagnosticOrder).where(DoctorDiagnosticOrder.visit_id.in_(visit_ids))
                diag_orders = (await self.db.execute(diag_q)).scalars().all()
                
                for diag in diag_orders:
                    _add_charge(diag.test_name, "Diagnostics")
        except Exception as e:
            logger.warning(f"[BRIDGE] Could not fetch diagnostic charges: {e}")
        
        return charges
    # ─── 6. Sync Pharmacy Dispensing to RCM Billing ────────────────────────
    async def push_pharmacy_charge_to_billing(
        self, patient_id: uuid.UUID, visit_id: uuid.UUID,
        medication_name: str, quantity: float, unit_price: float,
        org_id: uuid.UUID
    ):
        """When pharmacy dispenses, push the financial charge to the RCM master bill."""
        from app.core.rcm_billing.models import BillingMaster, BillingService, BillStatus
        from sqlalchemy import select
        
        # 1. Find the most recent active bill for this visit
        # We look for ANY bill because even if it's 'paid', we might need to add supplementary charges
        stmt = select(BillingMaster).where(
            BillingMaster.visit_id == visit_id,
            BillingMaster.patient_id == patient_id,
            BillingMaster.org_id == org_id
        ).order_by(BillingMaster.generated_at.desc()).limit(1)
        
        bill = (await self.db.execute(stmt)).scalars().first()
        
        if not bill:
            logger.warning(f"[BRIDGE] No RCM bill found for {patient_id} visit {visit_id} - skipping auto-charge")
            return
            
        # 2. Add the service line item
        total_cost = float(quantity) * float(unit_price)
        svc = BillingService(
            bill_id=bill.id,
            service_name=f"Pharmacy: {medication_name}",
            department="PHARMACY",
            base_rate=unit_price,
            quantity=int(quantity),
            total_cost=total_cost,
            is_auto_billed=True,
            org_id=org_id
        )
        self.db.add(svc)
        
        # 3. Update the bill heading amounts (if it's not fully locked/archived)
        if bill.status in [BillStatus.draft, BillStatus.unpaid, BillStatus.partially_paid, BillStatus.paid]:
            # Recalculate totals
            bill.gross_amount = float(bill.gross_amount) + total_cost
            bill.net_amount = float(bill.net_amount) + total_cost
            bill.balance_amount = float(bill.balance_amount) + total_cost
        
        await self.db.flush()
        logger.info(f"[BRIDGE] Pushed Pharmacy Charge ({medication_name}: ₹{total_cost}) to Bill {bill.bill_number}")

    # ─── 7. Initialize Master Bill for an Encounter ─────────────────────────
    async def initialize_bill(
        self, patient_id: uuid.UUID, visit_id: uuid.UUID,
        generated_by: uuid.UUID, org_id: uuid.UUID,
        encounter_type: str = "OPD"
    ) -> "BillingMaster":
        """Generates a default master billing heading for a new visit."""
        from app.core.rcm_billing.models import BillingMaster, BillStatus
        
        # Generate bill number based on encounter type and date
        prefix = "OPB" if encounter_type == "OPD" else "IPB"
        bill_no = f"{prefix}-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4().int)[:6]}"
        
        bill = BillingMaster(
            visit_id=visit_id,
            patient_id=patient_id,
            bill_number=bill_no,
            status=BillStatus.unpaid,
            generated_by=generated_by,
            gross_amount=0.0,
            net_amount=0.0,
            balance_amount=0.0,
            org_id=org_id
        )
        self.db.add(bill)
        await self.db.flush()
        logger.info(f"[BRIDGE] Initialized {encounter_type} Master Bill {bill_no} for Patient {patient_id}")
        return bill
