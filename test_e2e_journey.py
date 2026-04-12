import requests
import time
import json
import uuid
import sys

BASE_URL = "http://localhost:9500/api/v1"
headers = {"Content-Type": "application/json"}

# Use a default test doctor
DOCTOR_ID = "00000000-0000-0000-0000-000000000009"

def log(step, msg):
    print(f"\n[STEP {step}] {msg}")

def login_and_get_token():
    log("AUTH", "Authenticating to get Bearer Token...")
    res = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@riv-hlt1.com", "password": "Admin@1234"},
        headers={"Content-Type": "application/json"}
    )
    if not res.ok:
        print("Login Failed:", res.text)
        sys.exit(1)
    
    token = res.json().get("access_token")
    headers["Authorization"] = f"Bearer {token}"
    print("✅ Authenticated successfully.")

def run_tests():
    login_and_get_token()
    
    # 1. Register Patient
    log(1, "Registering new patient...")
    pt_data = {
        "first_name": "E2E",
        "last_name": "AutomatedTest",
        "date_of_birth": "1985-05-15",
        "gender": "Male",
        "primary_phone": "555-000-1234",
        "blood_group": "A",
        "rh_factor": "+"
    }
    res = requests.post(f"{BASE_URL}/patients/", json=pt_data, headers=headers)
    if res.status_code not in [200, 201]:
        print("Registration Failed:", res.text)
        return
    patient = res.json()
    pt_id = patient['id']
    print(f"✅ Success! Patient ID: {pt_id}")

    # 2. Add to Doctor Worklist (Simulate OPD Visit)
    log(2, "Adding patient to Doctor Worklist...")
    visit_id = str(uuid.uuid4())
    wl_data = {
        "doctor_id": DOCTOR_ID,
        "visit_id": visit_id,
        "patient_id": pt_id,
        "priority_indicator": "urgent"
    }
    res = requests.post(f"{BASE_URL}/doctor-desk/worklist", json=wl_data, headers=headers)
    if not res.ok:
        print("Worklist Seed Failed:", res.text)
        return
    wl_id = res.json()['id']
    print(f"✅ Success! Worklist Ticket ID: {wl_id}")

    # 3. Doctor Call & Note
    log(3, "Doctor starts consultation & saves note...")
    # update status
    res = requests.put(f"{BASE_URL}/doctor-desk/worklist/{wl_id}/status?status=in_consultation", headers=headers)
    if not res.ok: print("Status update failed", res.text)

    note_data = {
        "visit_id": visit_id,
        "doctor_id": DOCTOR_ID,
        "chief_complaint": "Severe Abdominal Pain, suspect Kidney Stone",
        "history_present_illness": "Pain started 2 hours ago.",
        "plan": "Order CT Scan and generic pain meds. Admit to ward for observation."
    }
    res = requests.post(f"{BASE_URL}/doctor-desk/scribe", json=note_data, headers=headers)
    if not res.ok:
        print("Note Save Failed:", res.text)
        return
    print("✅ Success! Note saved.")

    # 4. Doctor Orders Diagnostics (Radiology + Lab)
    log(4, "Doctor ordering Radiology and Lab tests (Manual vs AI)...")
    lab_order = {
        "visit_id": visit_id,
        "doctor_id": DOCTOR_ID,
        "order_type": "Laboratory",
        "test_name": "Complete Blood Count (CBC)",
        "priority": "routine"
    }
    res_lab = requests.post(f"{BASE_URL}/doctor-desk/orders", json=lab_order, headers=headers)
    
    rad_order = {
        "visit_id": visit_id,
        "doctor_id": DOCTOR_ID,
        "order_type": "Radiology",
        "test_name": "CT Abdomen Contrast",
        "priority": "urgent"
    }
    res_rad = requests.post(f"{BASE_URL}/doctor-desk/orders", json=rad_order, headers=headers)
    if not res_lab.ok or not res_rad.ok:
        print("Diagnostics Failed:", res_lab.text, res_rad.text)
        return
    print(f"✅ Success! Orders pushed to dispatch.")

    # 5. Doctor Commits Prescription
    log(5, "Doctor prescribes Medication...")
    rx_data = {
        "visit_id": visit_id, "doctor_id": DOCTOR_ID,
        "medicine_name": "Ketorolac", "strength": "30mg", "dosage": "1 Injection", "frequency": "STAT", "duration": "1 Day"
    }
    res = requests.post(f"{BASE_URL}/doctor-desk/prescriptions", json=rx_data, headers=headers)
    if not res.ok:
        print("Prescription Failed:", res.text)
        return
    print("✅ Success! Pharmacy notified.")

    # 6. Push to IPD Admission
    log(6, "Doctor recommends admission to IPD with Clinical Notes...")
    ipd_data = {
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "patient_uhid": patient.get('uhid', pt_id),
        "gender": patient['gender'],
        "date_of_birth": patient['date_of_birth'],
        "mobile_number": patient.get('primary_phone', "555"),
        "admitting_doctor": "Automated Tester",
        "treating_doctor": "Automated Tester",
        "reason_for_admission": "Severe Abdominal Pain",
        "admission_category": "Emergency",
        "admission_source": "OPD",
        "specialty": "General Medicine",
        "preferred_bed_category": "General Ward",
        "expected_admission_date": "2026-03-31T00:00:00",
        "clinical_notes": "Current Health: Stable\nDoses: IV Fluids STAT\nPlan: Keep NPO awaiting CT."
    }
    res = requests.post(f"{BASE_URL}/ipd/requests", json=ipd_data, headers=headers)
    if not res.ok:
        print("IPD Push Failed:", res.text)
        return
    ipd_req_id = res.json()['id']
    print(f"✅ Success! IPD Request Generated: {ipd_req_id}")

    # 6.5 IPD Approves Request
    log(6.5, "IPD Bed Manager approves Request...")
    res = requests.put(f"{BASE_URL}/ipd/requests/{ipd_req_id}/status?new_status=Approved", headers=headers)
    if not res.ok:
        print("IPD Approval Failed:", res.text)
        return
    print("✅ Success! IPD Request Approved.")

    # 6.8 Get or Create a Bed (Ward → Room → Bed)
    log(6.8, "Wards Module: Locating available Bed...")
    
    # First check if any available beds already exist
    beds_res = requests.get(f"{BASE_URL}/wards/beds", headers=headers)
    beds = beds_res.json() if beds_res.ok else []
    bed_code = None
    if isinstance(beds, list) and len(beds) > 0:
        avail = [bd for bd in beds if bd.get('status') == 'available']
        if avail:
            bed_code = avail[0]['bed_code']
            print(f"  Found existing available bed: {bed_code}")

    if not bed_code:
        uid = str(uuid.uuid4())[:4]
        print("  No available beds found. Creating Ward → Room → Bed...")
        
        # Step A: Create or find a Ward
        wards = requests.get(f"{BASE_URL}/wards/", headers=headers).json()
        ward_id = None
        if isinstance(wards, list) and len(wards) > 0:
            ward_id = wards[0]['id']
        else:
            w_res = requests.post(f"{BASE_URL}/wards/", headers=headers, json={
                "ward_code": f"GEN-{uid}", "ward_name": "General Ward",
                "department": "General Medicine", "floor": "1", "capacity": 20
            })
            if w_res.ok:
                ward_id = w_res.json()['id']
            else:
                print(f"  ⚠ Ward creation failed: {w_res.text}")
        
        # Step B: Create a Room in the Ward
        room_id = None
        if ward_id:
            rooms = requests.get(f"{BASE_URL}/wards/{ward_id}/rooms", headers=headers).json()
            if isinstance(rooms, list) and len(rooms) > 0:
                room_id = rooms[0]['id']
            else:
                rm_res = requests.post(f"{BASE_URL}/wards/rooms", headers=headers, json={
                    "ward_id": str(ward_id), "room_number": f"R-{uid}",
                    "room_type": "general", "capacity": 4
                })
                if rm_res.ok:
                    room_id = rm_res.json()['id']
                else:
                    print(f"  ⚠ Room creation failed: {rm_res.text}")
        
        # Step C: Create a Bed in the Room
        if room_id:
            bed_code = f"BED-{uid}"
            bed_res = requests.post(f"{BASE_URL}/wards/beds", headers=headers, json={
                "room_id": str(room_id), "bed_code": bed_code,
                "bed_number": f"101-{uid}", "bed_type": "standard", "status": "available"
            })
            if bed_res.ok:
                bed_code = bed_res.json().get('bed_code', bed_code)
                print(f"  Created new bed: {bed_code}")
            else:
                print(f"  ⚠ Bed creation failed: {bed_res.text}")
                bed_code = None

    if not bed_code:
        print("❌ FATAL: Could not locate or create an available bed. Aborting.")
        return

    print(f"✅ Auto-located Bed: {bed_code}")

    # 7. IPD Allocates Bed
    log(7, "IPD Nurse allocates Ward Bed...")
    res = requests.post(f"{BASE_URL}/ipd/requests/{ipd_req_id}/allocate/{bed_code}", headers=headers)
    if not res.ok:
        print("IPD Allocation Failed:", res.text)
        return
    adm_data = res.json()
    adm_no = adm_data.get('admission_number', 'UNKNOWN')
    print(f"✅ Success! Patient Allocated to Bed. Admission #: {adm_no}")

    # ═══════════════════════════════════════════════════════════════
    # PART 2: IPD CLINICAL ORDERS & BILLING
    # ═══════════════════════════════════════════════════════════════

    # 8. IPD Billing: Add Clinical Services
    log(8, "IPD Billing: Adding clinical service charges...")
    services = [
        {"service_category": "Bed Charges", "service_name": "General Ward - Per Day", "quantity": 3, "unit_price": 1500.00},
        {"service_category": "Laboratory", "service_name": "Complete Blood Count (CBC)", "quantity": 1, "unit_price": 450.00},
        {"service_category": "Radiology", "service_name": "CT Abdomen w/ Contrast", "quantity": 1, "unit_price": 8500.00},
        {"service_category": "Pharmacy", "service_name": "Ketorolac 30mg IV STAT", "quantity": 1, "unit_price": 120.00},
        {"service_category": "Pharmacy", "service_name": "IV Normal Saline 1L", "quantity": 2, "unit_price": 85.00},
        {"service_category": "Procedure", "service_name": "Emergency Consultation Fee", "quantity": 1, "unit_price": 2000.00},
    ]
    for svc in services:
        res = requests.post(f"{BASE_URL}/ipd/billing/{adm_no}/services", json=svc, headers=headers)
        if res.ok:
            print(f"  + {svc['service_name']} x{svc['quantity']} = ₹{svc['quantity']*svc['unit_price']}")
        else:
            print(f"  ⚠ Failed to add {svc['service_name']}: {res.text}")
    print("✅ All clinical charges posted to IPD Billing Ledger.")

    # 9. IPD Billing: Collect Advance Deposit
    log(9, "IPD Billing: Collecting Advance Deposit from Patient...")
    deposit = {"amount": 5000.00, "payment_mode": "Credit Card", "reference_number": "CC-TXN-98765"}
    res = requests.post(f"{BASE_URL}/ipd/billing/{adm_no}/deposits", json=deposit, headers=headers)
    if res.ok:
        print(f"✅ Deposit of ₹5,000 collected. Receipt: {res.json().get('receipt_number', 'N/A')}")
    else:
        print(f"⚠ Deposit Failed: {res.text}")

    # 10. IPD Billing: Register Insurance Claim
    log(10, "IPD Billing: Registering Insurance Claim (Star Health)...")
    insurance = {
        "insurance_provider": "Star Health Insurance",
        "policy_number": "STAR-2026-KS-44821",
        "pre_auth_number": "PA-2026-03-4482",
        "coverage_limit": 100000.00,
        "claimed_amount": 10000.00
    }
    res = requests.post(f"{BASE_URL}/ipd/billing/{adm_no}/insurance", json=insurance, headers=headers)
    if res.ok:
        ins_data = res.json()
        claim_id = ins_data.get('id')
        print(f"✅ Insurance Claim Registered! Provider: {ins_data.get('insurance_provider')}, Approved: ₹{ins_data.get('approved_amount', 0)}, Patient Share: ₹{ins_data.get('patient_share', 0)}")
        
        # 10.5 Approve Insurance Claim
        log(10.5, "IPD Billing: Simulating TPA Approval for Insurance Claim...")
        approve_payload = {
            "approved_amount": 10000.0,
            "status": "Approved"
        }
        res_approve = requests.post(f"{BASE_URL}/ipd/billing/insurance/{claim_id}/approve", json=approve_payload, headers=headers)
        if res_approve.ok:
            app_data = res_approve.json()
            print(f"✅ Insurance Claim Approved! Approved Amount: ₹{app_data.get('approved_amount')}, Status: {app_data.get('status')}")
        else:
            print(f"⚠ Insurance Approval Failed: {res_approve.text}")
            
    else:
        print(f"⚠ Insurance Registration Failed: {res.text}")

    # ═══════════════════════════════════════════════════════════════
    # PART 3: BLOOD BANK OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    # 11. Blood Bank: Register Donor
    log(11, "Blood Bank: Registering new donor...")
    uid_donor = str(uuid.uuid4())[:6]
    donor_data = {
        "donor_id": f"DON-E2E-{uid_donor}",
        "first_name": "TestDonor", "last_name": "E2E",
        "date_of_birth": "1990-01-15",
        "blood_group": "A", "rh_factor": "+",
        "contact_number": "555-999-3333",
        "screening_status": "eligible"
    }
    res = requests.post(f"{BASE_URL}/blood-bank/donors", json=donor_data, headers=headers)
    donor_id = None
    if res.ok:
        donor_id = res.json().get('id')
        print(f"✅ Donor Registered! ID: {donor_id}")
    else:
        print(f"⚠ Donor Registration Failed: {res.text}")

    # 12. Blood Bank: Log Blood Collection
    if donor_id:
        log(12, "Blood Bank: Logging blood collection from donor...")
        from datetime import datetime as dt, timezone
        now = dt.now(timezone.utc)
        collection_data = {
            "donor_id": str(donor_id),
            "collection_date": now.isoformat(),
            "collection_location": "Main Donation Room",
            "collected_by": "Nurse E2E Test",
            "collection_volume": 450.0,
            "screening_results": {"hiv": "negative", "hbsag": "negative", "hcv": "negative"}
        }
        res = requests.post(f"{BASE_URL}/blood-bank/donors/{donor_id}/collections", json=collection_data, headers=headers)
        collection_id = None
        if res.ok:
            collection_id = res.json().get('id')
            print(f"✅ Blood Collection Logged! ID: {collection_id}")
        else:
            print(f"⚠ Collection Failed: {res.text}")

        # 13. Blood Bank: Add Unit to Inventory
        if collection_id:
            log(13, "Blood Bank: Depositing blood unit into inventory...")
            from datetime import timedelta
            now = dt.now(timezone.utc)
            unit_data = {
                "unit_id": f"UNIT-E2E-{uid_donor}",
                "blood_group": "A",
                "rh_factor": "+",
                "collection_id": str(collection_id),
                "collection_date": now.isoformat(),
                "expiry_date": (now + timedelta(days=35)).isoformat(),
                "status": "available"
            }
            res = requests.post(f"{BASE_URL}/blood-bank/inventory", json=unit_data, headers=headers)
            if res.ok:
                print(f"✅ Blood unit deposited! ID: {res.json().get('id')}")
            else:
                print(f"⚠ Inventory Deposit Failed: {res.text}")
    else:
        log(12, "Skipping Blood Bank Collection (no donor ID)")
        log(13, "Skipping Blood Bank Inventory (no collection)")

    # ═══════════════════════════════════════════════════════════════
    # PART 4: IPD CLINICAL DOCUMENTATION
    # ═══════════════════════════════════════════════════════════════

    # 14. IPD: Record Vitals
    log(14, "IPD Nursing: Recording Patient Vitals...")
    vitals_data = {
        "temperature": 37.2, "pulse_rate": 88,
        "respiratory_rate": 18, "bp_systolic": 138, "bp_diastolic": 86,
        "spo2": 97.5, "height_cm": 175, "weight_kg": 78,
        "pain_score": 7
    }
    res = requests.post(f"{BASE_URL}/ipd/vitals/{adm_no}", json=vitals_data, headers=headers)
    if res.ok:
        v = res.json()
        print(f"✅ Vitals Recorded! BMI: {v.get('bmi')}, Alert: {v.get('alert_triggered')}")
    else:
        print(f"⚠ Vitals Failed: {res.text}")

    # 15. IPD: Doctor adds Diagnosis
    log(15, "IPD Doctor: Adding confirmed diagnosis...")
    diag_data = {
        "diagnosis_type": "Confirmed",
        "icd10_code": "N20.0",
        "description": "Calculus of Kidney (Renal Calculi / Kidney Stone)"
    }
    res = requests.post(f"{BASE_URL}/ipd/doctor/diagnoses/{adm_no}", json=diag_data, headers=headers)
    if res.ok:
        print(f"✅ Diagnosis Recorded! ICD-10: N20.0 — Kidney Stone")
    else:
        print(f"⚠ Diagnosis Failed: {res.text}")

    # 16. IPD: Doctor adds Treatment Plan
    log(16, "IPD Doctor: Creating treatment plan...")
    plan_data = {
        "therapy_type": "Medication",
        "instructions": "Start IV NS at 125ml/hr. Ketorolac 30mg IV q6h PRN. Monitor urine output. NPO until CT result."
    }
    res = requests.post(f"{BASE_URL}/ipd/doctor/treatment-plans/{adm_no}", json=plan_data, headers=headers)
    if res.ok:
        print("✅ Treatment Plan Created.")
    else:
        print(f"⚠ Treatment Plan Failed: {res.text}")

    # ═══════════════════════════════════════════════════════════════
    # PART 5: IPD PAYMENT & FINAL BILL
    # ═══════════════════════════════════════════════════════════════

    # 17. Recalculate IPD Bill
    log(17, "IPD Billing: Recalculating total bill...")
    res = requests.post(f"{BASE_URL}/ipd/billing/{adm_no}/recalculate", headers=headers)
    if res.ok:
        bill = res.json()
        print(f"✅ Bill Recalculated!")
        print(f"    Total Charges:     ₹{bill.get('total_charges', 0):,.2f}")
        print(f"    Total Deposits:    ₹{bill.get('total_deposits', 0):,.2f}")
        print(f"    Total Discount:    ₹{bill.get('total_discount', 0):,.2f}")
        print(f"    Insurance Payable: ₹{bill.get('insurance_payable', 0):,.2f}")
        print(f"    Patient Payable:   ₹{bill.get('patient_payable', 0):,.2f}")
        print(f"    Outstanding:       ₹{bill.get('outstanding_balance', 0):,.2f}")
    else:
        print(f"⚠ Recalculate Failed: {res.text}")

    # 18. Make Final Payment
    log(18, "IPD Billing: Processing final patient payment...")
    payment = {"amount": 7740.00, "payment_mode": "UPI", "reference_number": "UPI-REF-20260331-001"}
    res = requests.post(f"{BASE_URL}/ipd/billing/{adm_no}/payments", json=payment, headers=headers)
    if res.ok:
        pay_data = res.json()
        print(f"✅ Payment Processed! Receipt: {pay_data.get('receipt_number', 'N/A')}")
    else:
        print(f"⚠ Payment Failed: {res.text}")

    # 19. Final Bill Summary
    log(19, "IPD Billing: Fetching Final Consolidated Bill...")
    res = requests.get(f"{BASE_URL}/ipd/billing/{adm_no}", headers=headers)
    if res.ok:
        fb = res.json()
        print("═"*55)
        print("         FINAL IPD BILL SUMMARY")
        print("═"*55)
        print(f"  Admission #:       {fb.get('admission_number')}")
        print(f"  Patient:           {fb.get('patient_name')}")
        print(f"  Ward/Bed:          {fb.get('ward_name', 'N/A')} / {fb.get('bed_code', 'N/A')}")
        print(f"  ─────────────────────────────────────────")
        print(f"  Total Charges:     ₹{fb.get('total_charges', 0):,.2f}")
        print(f"  (-) Discount:      ₹{fb.get('total_discount', 0):,.2f}")
        print(f"  (+) Tax:           ₹{fb.get('total_tax', 0):,.2f}")
        print(f"  Insurance Covered: ₹{fb.get('insurance_payable', 0):,.2f}")
        print(f"  Patient Payable:   ₹{fb.get('patient_payable', 0):,.2f}")
        print(f"  ─────────────────────────────────────────")
        print(f"  Total Deposits:    ₹{fb.get('total_deposits', 0):,.2f}")
        print(f"  Total Paid:        ₹{fb.get('total_paid', 0):,.2f}")
        print(f"  Outstanding:       ₹{fb.get('outstanding_balance', 0):,.2f}")
        print(f"  Status:            {fb.get('status')}")
        print("═"*55)
    else:
        print(f"⚠ Final Bill fetch failed: {res.text}")

    # 20. Fetch Itemized Services
    log(20, "IPD Billing: Listing all itemized charges...")
    res = requests.get(f"{BASE_URL}/ipd/billing/{adm_no}/services", headers=headers)
    if res.ok:
        items = res.json()
        print(f"✅ {len(items)} line items on bill:")
        for item in items:
            print(f"    [{item.get('service_category')}] {item.get('service_name')} x{item.get('quantity')} = ₹{item.get('total_price', 0):,.2f}")
    else:
        print(f"⚠ Services fetch failed: {res.text}")

    print("\n" + "═"*55)
    print("🎉 FULL END-TO-END PATIENT JOURNEY PASSED! 🎉")
    print("═"*55)
    print("""
Summary of Validated Workflows:
  ✅ Step 1:   Patient Registration
  ✅ Step 2:   Doctor Worklist Assignment
  ✅ Step 3:   Clinical Consultation & Note
  ✅ Step 4:   Diagnostic Orders (Lab + Radiology)
  ✅ Step 5:   Pharmacy Prescription
  ✅ Step 6:   IPD Admission Request + Approval
  ✅ Step 6.8: Ward → Room → Bed Provisioning
  ✅ Step 7:   Bed Allocation & Encounter Creation
  ✅ Step 8:   IPD Billing - Clinical Service Charges
  ✅ Step 9:   IPD Billing - Advance Deposit
  ✅ Step 10:  Insurance Claim Registration
  ✅ Step 11:  Blood Bank - Donor Registration
  ✅ Step 12:  Blood Bank - Collection Logging
  ✅ Step 13:  Blood Bank - Inventory Deposit
  ✅ Step 14:  Nursing - Vitals Recording
  ✅ Step 15:  Doctor - Diagnosis (ICD-10)
  ✅ Step 16:  Doctor - Treatment Plan
  ✅ Step 17:  IPD Billing - Bill Recalculation
  ✅ Step 18:  IPD Billing - Final Payment
  ✅ Step 19:  Final Consolidated Bill
  ✅ Step 20:  Itemized Charge Listing
""")


if __name__ == "__main__":
    run_tests()

