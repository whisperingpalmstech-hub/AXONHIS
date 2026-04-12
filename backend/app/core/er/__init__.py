"""
AXONHIS Emergency Room (ER) Module
====================================
Complete ER workflow per FRD: Registration (urgent/normal), ESI Triage,
Bed Allocation (zone-based), Nursing/Doctor Coversheets, MLC Management,
Scoring Systems, Discharge Workflow, and Digital Command Center Dashboard.

Interconnections:
- Patient Registration → patients module
- Billing → billing_masters (PricingEngine) + rcm_billing (BillingMaster)
- Lab/Radiology → orders module for test ordering
- Pharmacy → pharmacy module for medication dispensing
- IPD → ipd module for ER-to-IPD admission transfer
- Nursing → nursing_triage module for vitals + scoring
- Wards → wards module for bed management

FRD Reference: HIMS_ER_Module_FRD.docx
"""
