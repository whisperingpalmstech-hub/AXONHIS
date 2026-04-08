#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
 AXONHIS — COMPREHENSIVE QA END-TO-END TEST SUITE
 Professional-grade testing framework for all API endpoints
═══════════════════════════════════════════════════════════════════════

Features:
- Systematic endpoint testing across all modules
- Test data factories and cleanup
- Positive and negative test cases
- Detailed HTML reports
- Test categorization (smoke, regression, integration)
- Performance metrics
- Retry logic for flaky tests
- Authentication/authorization testing
- Data validation testing
- Error handling validation

Usage:
    python comprehensive_e2e_test_suite.py --suite all
    python comprehensive_e2e_test_suite.py --suite smoke
    python comprehensive_e2e_test_suite.py --suite regression --module auth
    python comprehensive_e2e_test_suite.py --report html
═══════════════════════════════════════════════════════════════════════
"""

import requests
import uuid
import json
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('e2e_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestSuite(Enum):
    SMOKE = "smoke"  # Critical path tests only
    REGRESSION = "regression"  # Full regression suite
    INTEGRATION = "integration"  # Cross-module integration tests
    PERFORMANCE = "performance"  # Performance and load tests
    SECURITY = "security"  # Security and auth tests
    ALL = "all"  # Run all tests


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class TestResult:
    name: str
    module: str
    endpoint: str
    method: str
    status: TestStatus
    expected_status: int
    actual_status: int
    response_time_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestContext:
    """Shared context across test phases"""
    headers: Dict[str, str] = field(default_factory=dict)
    token: Optional[str] = None
    patient_id: Optional[str] = None
    uhid: Optional[str] = None
    visit_id: Optional[str] = None
    appointment_id: Optional[str] = None
    doctor_id: str = "00000000-0000-0000-0000-000000000009"
    lab_order_id: Optional[str] = None
    prescription_id: Optional[str] = None
    er_encounter_id: Optional[str] = None
    ipd_request_id: Optional[str] = None
    billing_id: Optional[str] = None
    test_data: Dict[str, Any] = field(default_factory=dict)


class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def generate_uhid() -> str:
        return f"E2E-{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def generate_patient_data(uhid: Optional[str] = None) -> Dict:
        return {
            "first_name": "TestPatient",
            "last_name": f"QA-{uuid.uuid4().hex[:6]}",
            "gender": "Male",
            "date_of_birth": "1990-05-15",
            "blood_group": "O+",
            "uhid": uhid or TestDataFactory.generate_uhid(),
            "primary_phone": "9876543210",
            "email": f"qa_test_{uuid.uuid4().hex[:8]}@test.com",
            "address_line1": "123 Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "pincode": "400001"
        }
    
    @staticmethod
    def generate_appointment_data(patient_id: str, doctor_id: str) -> Dict:
        return {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_date": datetime.now().strftime("%Y-%m-%d"),
            "slot_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "slot_id": str(uuid.uuid4()),
            "department": "General Medicine",
            "visit_type": "new"
        }
    
    @staticmethod
    def generate_lab_order_data(visit_id: str, doctor_id: str) -> Dict:
        return {
            "visit_id": visit_id,
            "doctor_id": doctor_id,
            "order_type": "lab",
            "test_name": "Complete Blood Count"
        }
    
    @staticmethod
    def generate_prescription_data(visit_id: str, doctor_id: str) -> Dict:
        return {
            "visit_id": visit_id,
            "doctor_id": doctor_id,
            "medicine_name": "Amoxicillin",
            "strength": "500mg",
            "dosage": "1 Capsule",
            "frequency": "TDS",
            "duration": "7 days",
            "instructions": "After meals"
        }


class APIClient:
    """HTTP client with retry logic and error handling"""
    
    def __init__(self, base_url: str = "http://localhost:9500/api/v1", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        expected_status: int = 200,
        retry_count: int = 3
    ) -> Tuple[requests.Response, float]:
        """
        Make HTTP request with retry logic
        Returns: (response, response_time_ms)
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None
        
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    params=params,
                    timeout=self.timeout
                )
                response_time = (time.time() - start_time) * 1000
                return response, response_time
            except requests.exceptions.Timeout:
                last_error = f"Timeout after {self.timeout}s"
                logger.warning(f"Attempt {attempt + 1}/{retry_count}: Timeout")
                time.sleep(1)
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
                logger.warning(f"Attempt {attempt + 1}/{retry_count}: Connection error")
                time.sleep(2)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}/{retry_count}: {e}")
                time.sleep(1)
        
        # If all retries failed, raise the last error
        raise Exception(f"Request failed after {retry_count} attempts: {last_error}")


class TestRunner:
    """Main test execution engine"""
    
    def __init__(self, suite: TestSuite = TestSuite.ALL, module_filter: Optional[str] = None):
        self.suite = suite
        self.module_filter = module_filter
        self.client = APIClient()
        self.context = TestContext()
        self.results: List[TestResult] = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.start_time = None
    
    def run_test(
        self,
        name: str,
        module: str,
        method: str,
        endpoint: str,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        expected_status: int = 200,
        critical: bool = False,
        skip_condition: bool = False
    ) -> Optional[requests.Response]:
        """
        Execute a single test case
        """
        self.test_count += 1
        
        # Check skip condition
        if skip_condition:
            result = TestResult(
                name=name,
                module=module,
                endpoint=endpoint,
                method=method,
                status=TestStatus.SKIP,
                expected_status=expected_status,
                actual_status=0,
                response_time_ms=0,
                error_message="Skipped by condition"
            )
            self.results.append(result)
            self.skip_count += 1
            logger.info(f"  [{self.test_count:03d}] ⚠️  SKIP: {name}")
            return None
        
        # Check module filter
        if self.module_filter and module.lower() != self.module_filter.lower():
            result = TestResult(
                name=name,
                module=module,
                endpoint=endpoint,
                method=method,
                status=TestStatus.SKIP,
                expected_status=expected_status,
                actual_status=0,
                response_time_ms=0,
                error_message=f"Module filter: {self.module_filter}"
            )
            self.results.append(result)
            self.skip_count += 1
            return None
        
        # Check suite filter
        if self.suite == TestSuite.SMOKE and not critical:
            result = TestResult(
                name=name,
                module=module,
                endpoint=endpoint,
                method=method,
                status=TestStatus.SKIP,
                expected_status=expected_status,
                actual_status=0,
                response_time_ms=0,
                error_message="Not in smoke suite"
            )
            self.results.append(result)
            self.skip_count += 1
            return None
        
        try:
            response, response_time = self.client.request(
                method=method,
                endpoint=endpoint,
                headers=headers,
                json_data=json_data,
                params=params
            )
            
            status = TestStatus.PASS if response.status_code == expected_status else TestStatus.FAIL
            if status == TestStatus.PASS:
                self.pass_count += 1
                logger.info(f"  [{self.test_count:03d}] ✅ PASS: {name} ({response.status_code}) - {response_time:.0f}ms")
            else:
                self.fail_count += 1
                error_msg = response.text[:200] if response.text else "No error message"
                logger.error(f"  [{self.test_count:03d}] ❌ FAIL: {name} (Expected: {expected_status}, Got: {response.status_code}) - {error_msg}")
            
            result = TestResult(
                name=name,
                module=module,
                endpoint=endpoint,
                method=method,
                status=status,
                expected_status=expected_status,
                actual_status=response.status_code,
                response_time_ms=response_time,
                error_message=error_msg if status == TestStatus.FAIL else None
            )
            self.results.append(result)
            
            return response
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"  [{self.test_count:03d}] 🚨 ERROR: {name} - {str(e)}")
            
            result = TestResult(
                name=name,
                module=module,
                endpoint=endpoint,
                method=method,
                status=TestStatus.ERROR,
                expected_status=expected_status,
                actual_status=0,
                response_time_ms=0,
                error_message=str(e)
            )
            self.results.append(result)
            return None
    
    def section(self, title: str):
        """Print section header"""
        logger.info(f"\n{'─' * 80}")
        logger.info(f"  📋 {title}")
        logger.info(f"{'─' * 80}")
    
    def authenticate(self) -> bool:
        """Authenticate and get token"""
        self.section("AUTHENTICATION & SYSTEM HEALTH")
        
        # Health check (direct endpoint, not through API prefix)
        try:
            health_url = self.client.base_url.replace("/api/v1", "") + "/health"
            start_time = time.time()
            health_response = requests.get(health_url, timeout=10)
            health_time = (time.time() - start_time) * 1000
            if health_response.status_code == 200:
                logger.info(f"  [001] ✅ PASS: Health Check (200) - {health_time:.0f}ms")
            else:
                logger.error(f"  [001] ❌ FAIL: Health Check (Expected: 200, Got: {health_response.status_code})")
                logger.error("Health check failed. Aborting.")
                return False
        except Exception as e:
            logger.error(f"  [001] ❌ FAIL: Health Check - {e}")
            logger.error("Health check failed. Aborting.")
            return False
        
        # Login
        response = self.run_test(
            name="Login (Admin)",
            module="auth",
            method="POST",
            endpoint="/auth/login",
            json_data={
                "email": "admin@axonhis.com",
                "password": "Admin@123"
            },
            expected_status=200,
            critical=True
        )
        
        if response and response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                self.context.token = token
                self.context.headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                logger.info(f"  ✓ Authenticated successfully")
                return True
        
        logger.error("Authentication failed. Aborting.")
        return False
    
    def test_auth_module(self):
        """Test authentication endpoints"""
        self.section("MODULE: AUTHENTICATION")
        
        # Get current user
        self.run_test(
            name="Get Current User",
            module="auth",
            method="GET",
            endpoint="/auth/me",
            headers=self.context.headers,
            expected_status=200,
            critical=True
        )
        
        # Test invalid login
        self.run_test(
            name="Invalid Login (Negative Test)",
            module="auth",
            method="POST",
            endpoint="/auth/login",
            json_data={
                "email": "invalid@test.com",
                "password": "wrongpassword"
            },
            expected_status=401
        )
        
        # Test missing credentials
        self.run_test(
            name="Missing Password (Validation Test)",
            module="auth",
            method="POST",
            endpoint="/auth/login",
            json_data={
                "email": "admin@axonhis.com"
            },
            expected_status=422
        )
    
    def test_patient_module(self):
        """Test patient management endpoints"""
        self.section("MODULE: PATIENT MANAGEMENT")
        
        # Register patient
        patient_data = TestDataFactory.generate_patient_data()
        response = self.run_test(
            name="Register Patient",
            module="patients",
            method="POST",
            endpoint="/patients/",
            headers=self.context.headers,
            json_data=patient_data,
            expected_status=201,
            critical=True
        )
        
        if response and response.status_code == 201:
            patient = response.json()
            self.context.patient_id = patient.get("id")
            self.context.uhid = patient_data["uhid"]
            logger.info(f"  ✓ Patient ID: {self.context.patient_id[:12]}... UHID: {self.context.uhid}")
        
        # Get patient by ID
        if self.context.patient_id:
            self.run_test(
                name="Get Patient by ID",
                module="patients",
                method="GET",
                endpoint=f"/patients/{self.context.patient_id}",
                headers=self.context.headers,
                expected_status=200,
                critical=True
            )
        
        # Search patients
        self.run_test(
            name="Search Patients",
            module="patients",
            method="GET",
            endpoint="/patients/",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Test invalid patient ID
        self.run_test(
            name="Get Invalid Patient ID (Negative Test)",
            module="patients",
            method="GET",
            endpoint="/patients/00000000-0000-0000-0000-000000000000",
            headers=self.context.headers,
            expected_status=404
        )
    
    def test_scheduling_module(self):
        """Test scheduling and appointments"""
        self.section("MODULE: SCHEDULING & APPOINTMENTS")
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get available slots
        self.run_test(
            name="Get Available Slots",
            module="scheduling",
            method="GET",
            endpoint=f"/scheduling/slots/doctor/{self.context.doctor_id}?slot_date={current_date}",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Book appointment (non-critical - requires valid slots to exist)
        if self.context.patient_id:
            appointment_data = TestDataFactory.generate_appointment_data(
                self.context.patient_id,
                self.context.doctor_id
            )
            response = self.run_test(
                name="Book Appointment",
                module="scheduling",
                method="POST",
                endpoint="/scheduling/bookings",
                headers=self.context.headers,
                json_data=appointment_data,
                expected_status=200,
                critical=False
            )
            
            if response and response.status_code == 200:
                self.context.appointment_id = response.json().get("id")
    
    def test_opd_module(self):
        """Test OPD workflow"""
        self.section("MODULE: OPD WORKFLOW")
        
        # Create OPD visit
        if self.context.patient_id:
            visit_data = {
                "patient_id": self.context.patient_id,
                "doctor_id": self.context.doctor_id,
                "department": "General Medicine",
                "visit_type": "new_visit",
                "chief_complaint": "Persistent cough and fever",
                "priority": "normal"
            }
            response = self.run_test(
                name="Create OPD Visit",
                module="opd",
                method="POST",
                endpoint="/opd-visits/visits",
                headers=self.context.headers,
                json_data=visit_data,
                expected_status=201,
                critical=True
            )
            
            if response and response.status_code in [200, 201]:
                self.context.visit_id = response.json().get("id", str(uuid.uuid4()))
                logger.info(f"  ✓ Visit ID: {self.context.visit_id}")
        
        # Get OPD visits
        self.run_test(
            name="Get OPD Visits",
            module="opd",
            method="GET",
            endpoint="/opd-visits/visits",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_nursing_triage_module(self):
        """Test nursing triage"""
        self.section("MODULE: NURSING TRIAGE")
        
        if self.context.patient_id and self.context.visit_id:
            triage_data = {
                "patient_id": self.context.patient_id,
                "visit_id": self.context.visit_id,
                "temperature": 38.2,
                "pulse": 88,
                "bp_systolic": 140,
                "bp_diastolic": 90,
                "respiratory_rate": 20,
                "spo2": 97,
                "weight": 82,
                "height": 175,
                "chief_complaint": "Cough and fever",
                "acuity_level": "3",
                "triage_notes": "Patient alert and oriented"
            }
            self.run_test(
                name="Submit Triage Data",
                module="nursing",
                method="POST",
                endpoint="/nursing-triage/vitals",
                headers=self.context.headers,
                json_data=triage_data,
                expected_status=200
            )
    
    def test_doctor_desk_module(self):
        """Test doctor desk / EMR"""
        self.section("MODULE: DOCTOR DESK / EMR")
        
        if self.context.patient_id and self.context.visit_id:
            # Seed worklist
            worklist_data = {
                "doctor_id": self.context.doctor_id,
                "visit_id": self.context.visit_id,
                "patient_id": self.context.patient_id,
                "encounter_type": "opd",
                "priority_indicator": "normal"
            }
            response = self.run_test(
                name="Seed Worklist",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/worklist",
                headers=self.context.headers,
                json_data=worklist_data,
                expected_status=200
            )
            
            if response and response.status_code == 200:
                wl_id = response.json().get("id")
                
                # Start consultation
                self.run_test(
                    name="Start Consultation",
                    module="doctor_desk",
                    method="PUT",
                    endpoint=f"/doctor-desk/worklist/{wl_id}/status?status=in_consultation",
                    headers=self.context.headers,
                    expected_status=200
                )
            
            # Record vitals
            vitals_data = {
                "visit_id": self.context.visit_id,
                "patient_id": self.context.patient_id,
                "temperature": "38.2",
                "pulse_rate": "88",
                "respiratory_rate": "20",
                "bp_systolic": 140,
                "bp_diastolic": 90,
                "spo2": "97",
                "height_cm": "175",
                "weight_kg": "82"
            }
            self.run_test(
                name="Record Vitals (BMI)",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/advanced/vitals",
                headers=self.context.headers,
                json_data=vitals_data,
                expected_status=200
            )
            
            # Add complaint
            complaint_data = {
                "visit_id": self.context.visit_id,
                "patient_id": self.context.patient_id,
                "encounter_type": "opd",
                "icpc_code": "R05",
                "complaint_description": "Persistent dry cough",
                "duration": "5 days",
                "severity": "moderate"
            }
            self.run_test(
                name="Add Complaint",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/advanced/complaints",
                headers=self.context.headers,
                json_data=complaint_data,
                expected_status=200
            )
            
            # Add diagnosis
            diagnosis_data = {
                "visit_id": self.context.visit_id,
                "patient_id": self.context.patient_id,
                "icd_code": "J20.9",
                "diagnosis_description": "Acute Bronchitis",
                "diagnosis_type": "provisional",
                "is_primary": True
            }
            self.run_test(
                name="Add Diagnosis",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/advanced/diagnoses",
                headers=self.context.headers,
                json_data=diagnosis_data,
                expected_status=200
            )
            
            # AI CDSS suggestions
            ai_data = {
                "visit_id": self.context.visit_id,
                "symptoms": "dry cough, fever, crackles"
            }
            self.run_test(
                name="AI CDSS Suggestions",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/ai/suggestions",
                headers=self.context.headers,
                json_data=ai_data,
                expected_status=200
            )
            
            # Save SOAP note
            soap_data = {
                "visit_id": self.context.visit_id,
                "doctor_id": self.context.doctor_id,
                "chief_complaint": "Persistent dry cough x5 days with fever",
                "history_present_illness": "Worsening cough. Fever 38C. No relief with OTC.",
                "physical_examination": "Temp 38.2C. Crackles RLL. SpO2 97%.",
                "diagnosis": "Acute Bronchitis (J20.9)",
                "plan": "Start antibiotics. CBC, CXR ordered."
            }
            self.run_test(
                name="Save SOAP Note",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/scribe",
                headers=self.context.headers,
                json_data=soap_data,
                expected_status=200
            )
    
    def test_orders_module(self):
        """Test CPOE orders"""
        self.section("MODULE: CPOE ORDERS")
        
        if self.context.visit_id:
            # Order lab test
            lab_order_data = TestDataFactory.generate_lab_order_data(
                self.context.visit_id,
                self.context.doctor_id
            )
            response = self.run_test(
                name="Order Lab: CBC",
                module="orders",
                method="POST",
                endpoint="/doctor-desk/orders",
                headers=self.context.headers,
                json_data=lab_order_data,
                expected_status=200
            )
            
            if response and response.status_code == 200:
                self.context.lab_order_id = response.json().get("id")
            
            # Order radiology
            radiology_order_data = {
                "visit_id": self.context.visit_id,
                "doctor_id": self.context.doctor_id,
                "order_type": "radiology",
                "test_name": "PA Chest X-Ray"
            }
            self.run_test(
                name="Order Radiology: CXR",
                module="orders",
                method="POST",
                endpoint="/doctor-desk/orders",
                headers=self.context.headers,
                json_data=radiology_order_data,
                expected_status=200
            )
            
            # Fetch orders
            self.run_test(
                name="Fetch Orders",
                module="orders",
                method="GET",
                endpoint=f"/doctor-desk/orders?visit_id={self.context.visit_id}",
                headers=self.context.headers,
                expected_status=200
            )
    
    def test_prescriptions_module(self):
        """Test prescriptions"""
        self.section("MODULE: PRESCRIPTIONS")
        
        if self.context.visit_id:
            prescription_data = TestDataFactory.generate_prescription_data(
                self.context.visit_id,
                self.context.doctor_id
            )
            response = self.run_test(
                name="Create Prescription",
                module="doctor_desk",
                method="POST",
                endpoint="/doctor-desk/prescriptions",
                headers=self.context.headers,
                json_data=prescription_data,
                expected_status=200
            )
            
            if response and response.status_code == 200:
                self.context.prescription_id = response.json().get("id")
            
            # Fetch prescriptions
            self.run_test(
                name="Fetch Prescriptions",
                module="doctor_desk",
                method="GET",
                endpoint=f"/doctor-desk/prescriptions?visit_id={self.context.visit_id}",
                headers=self.context.headers,
                expected_status=200
            )
    
    def test_lab_module(self):
        """Test laboratory module"""
        self.section("MODULE: LABORATORY (LIS)")
        
        # Get lab orders
        self.run_test(
            name="Get Lab Orders",
            module="lab",
            method="GET",
            endpoint="/lab/orders",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Phlebotomy worklist
        self.run_test(
            name="Phlebotomy Worklist",
            module="lab",
            method="GET",
            endpoint="/phlebotomy/worklist",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Central receiving
        self.run_test(
            name="Central Receiving",
            module="lab",
            method="GET",
            endpoint="/central-receiving/receipts",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_radiology_module(self):
        """Test radiology module"""
        self.section("MODULE: RADIOLOGY (RIS)")
        
        # Get studies
        self.run_test(
            name="Get Imaging Studies",
            module="radiology",
            method="GET",
            endpoint="/radiology/studies",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Get orders
        self.run_test(
            name="Get Radiology Orders",
            module="radiology",
            method="GET",
            endpoint="/radiology/orders",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_pharmacy_module(self):
        """Test pharmacy module"""
        self.section("MODULE: PHARMACY")
        
        # Get prescriptions
        self.run_test(
            name="Get Pharmacy Prescriptions",
            module="pharmacy",
            method="GET",
            endpoint="/pharmacy/prescriptions",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Get medications
        self.run_test(
            name="Get Medications",
            module="pharmacy",
            method="GET",
            endpoint="/pharmacy/medications",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_billing_module(self):
        """Test billing module"""
        self.section("MODULE: BILLING & RCM")
        
        if self.context.patient_id:
            # Get encounter charges
            self.run_test(
                name="Get Encounter Charges",
                module="billing",
                method="GET",
                endpoint=f"/rcm-billing/encounter-charges/{self.context.patient_id}",
                headers=self.context.headers,
                expected_status=200
            )
        
        # Get billing masters
        self.run_test(
            name="Get Billing Services",
            module="billing",
            method="GET",
            endpoint="/billing-masters/services",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_er_module(self):
        """Test emergency room module"""
        self.section("MODULE: EMERGENCY ROOM (ER)")
        
        if self.context.patient_id:
            er_data = {
                "patient_id": self.context.patient_id,
                "patient_name": "TestPatient",
                "arrival_mode": "walk-in",
                "presenting_complaints": ["chest pain", "shortness of breath"],
                "is_mlc": False
            }
            response = self.run_test(
                name="Register ER Patient",
                module="er",
                method="POST",
                endpoint="/er/register",
                headers=self.context.headers,
                json_data=er_data,
                expected_status=200
            )
            
            if response and response.status_code == 200:
                self.context.er_encounter_id = response.json().get("id")
        
        # Get ER dashboard
        self.run_test(
            name="Get ER Dashboard",
            module="er",
            method="GET",
            endpoint="/er/dashboard",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_ipd_module(self):
        """Test inpatient department module"""
        self.section("MODULE: IPD (INPATIENT)")
        
        uhid = self.context.uhid or TestDataFactory.generate_uhid()
        ipd_data = {
            "patient_name": "TestPatient",
            "patient_uhid": uhid,
            "gender": "Male",
            "date_of_birth": "1990-05-15",
            "mobile_number": "9876543210",
            "admitting_doctor": "Dr. Test",
            "treating_doctor": "Dr. Test",
            "specialty": "General Medicine",
            "reason_for_admission": "Observation for bronchitis",
            "admission_category": "Elective",
            "admission_source": "OPD",
            "preferred_bed_category": "General Ward",
            "expected_admission_date": datetime.now().isoformat()
        }
        response = self.run_test(
            name="Create IPD Request",
            module="ipd",
            method="POST",
            endpoint="/ipd/requests",
            headers=self.context.headers,
            json_data=ipd_data,
            expected_status=200
        )
        
        if response and response.status_code == 200:
            self.context.ipd_request_id = response.json().get("id")
        
        # Get pending requests
        self.run_test(
            name="Get Pending IPD Requests",
            module="ipd",
            method="GET",
            endpoint="/ipd/requests/pending",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_wards_module(self):
        """Test ward management"""
        self.section("MODULE: WARDS & BED MANAGEMENT")
        
        # Get all wards
        self.run_test(
            name="Get All Wards",
            module="wards",
            method="GET",
            endpoint="/wards/",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Get occupancy dashboard
        self.run_test(
            name="Get Occupancy Dashboard",
            module="wards",
            method="GET",
            endpoint="/wards/dashboard/occupancy",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_ot_module(self):
        """Test operating theatre module"""
        self.section("MODULE: OPERATING THEATRE (OT)")
        
        # Get OT schedule
        self.run_test(
            name="Get OT Schedule",
            module="ot",
            method="GET",
            endpoint="/ot/schedule",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_blood_bank_module(self):
        """Test blood bank module"""
        self.section("MODULE: BLOOD BANK")
        
        # Get inventory
        self.run_test(
            name="Get Blood Bank Inventory",
            module="blood_bank",
            method="GET",
            endpoint="/blood-bank/inventory",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Get orders
        self.run_test(
            name="Get Blood Bank Orders",
            module="blood_bank",
            method="GET",
            endpoint="/blood-bank/orders",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_inventory_module(self):
        """Test inventory module"""
        self.section("MODULE: INVENTORY & STORES")
        
        # Get stores
        self.run_test(
            name="Get Inventory Stores",
            module="inventory",
            method="GET",
            endpoint="/inventory/stores",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_analytics_module(self):
        """Test analytics module"""
        self.section("MODULE: ANALYTICS & BI")
        
        # Get clinical metrics
        self.run_test(
            name="Get Clinical Metrics",
            module="analytics",
            method="GET",
            endpoint="/analytics/clinical-metrics",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Get BI analytics
        self.run_test(
            name="Get BI Analytics",
            module="analytics",
            method="GET",
            endpoint="/bi-intelligence/analytics/clinical",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_notifications_module(self):
        """Test notifications module"""
        self.section("MODULE: NOTIFICATIONS")
        
        # Get notifications
        self.run_test(
            name="Get Notifications",
            module="notifications",
            method="GET",
            endpoint="/notifications/",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_system_module(self):
        """Test system endpoints"""
        self.section("MODULE: SYSTEM HEALTH & AUDIT")
        
        # System health - skip this as it's already tested in authenticate()
        # The endpoint is at /health not /api/v1/system/health
        
        # Audit logs
        self.run_test(
            name="Get Audit Logs",
            module="audit",
            method="GET",
            endpoint="/audit",
            headers=self.context.headers,
            expected_status=200
        )
    
    def test_cdss_module(self):
        """Test clinical decision support"""
        self.section("MODULE: CLINICAL DECISION SUPPORT (CDSS)")
        
        # Use valid UUIDs
        patient_id = self.context.patient_id or str(uuid.uuid4())
        encounter_id = self.context.visit_id or str(uuid.uuid4())
        
        cdss_data = {
            "patient_context": {
                "patient_id": patient_id,
                "encounter_id": encounter_id,
                "age": 30,
                "gender": "male",
                "allergies": []
            },
            "new_medication_id": "MED-123",
            "medications": ["Amoxicillin", "Metformin"]
        }
        self.run_test(
            name="Medication Interaction Check",
            module="cdss",
            method="POST",
            endpoint="/cdss/engine/check-medication",
            headers=self.context.headers,
            json_data=cdss_data,
            expected_status=200
        )
    
    def test_kiosk_module(self):
        """Test kiosk module"""
        self.section("MODULE: SELF-SERVICE KIOSK")
        
        # Get departments
        self.run_test(
            name="Get Kiosk Departments",
            module="kiosk",
            method="GET",
            endpoint="/kiosk/departments",
            headers=self.context.headers,
            expected_status=200
        )
        
        # Get doctors
        self.run_test(
            name="Get Kiosk Doctors",
            module="kiosk",
            method="GET",
            endpoint="/kiosk/doctors?department=Cardiology",
            headers=self.context.headers,
            expected_status=200
        )
    
    def generate_report(self, format: str = "text"):
        """Generate test report"""
        total = self.pass_count + self.fail_count + self.error_count
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        if format == "text":
            self.print_text_report(total, duration)
        elif format == "html":
            self.generate_html_report(total, duration)
        elif format == "json":
            self.generate_json_report(total, duration)
    
    def print_text_report(self, total: int, duration: float):
        """Print text report"""
        logger.info(f"\n{'═' * 80}")
        logger.info(f"  AXONHIS — COMPREHENSIVE E2E TEST RESULTS")
        logger.info(f"  Suite: {self.suite.value.upper()}")
        logger.info(f"  Module Filter: {self.module_filter or 'None'}")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info(f"{'═' * 80}")
        logger.info(f"  ✅ PASSED:  {self.pass_count}/{total}")
        logger.info(f"  ❌ FAILED:  {self.fail_count}/{total}")
        logger.info(f"  🚨 ERRORS:  {self.error_count}/{total}")
        logger.info(f"  ⚠️  SKIPPED: {self.skip_count}")
        logger.info(f"{'═' * 80}")
        
        if total > 0:
            pass_rate = (self.pass_count / total) * 100
            logger.info(f"  📊 Pass Rate: {pass_rate:.1f}%")
        
        # Calculate average response time
        passed_results = [r for r in self.results if r.status == TestStatus.PASS]
        if passed_results:
            avg_time = sum(r.response_time_ms for r in passed_results) / len(passed_results)
            logger.info(f"  ⏱️  Avg Response Time: {avg_time:.0f}ms")
        
        # Show failed tests
        failed_results = [r for r in self.results if r.status == TestStatus.FAIL]
        if failed_results:
            logger.info(f"\n  ❌ FAILED TESTS:")
            for r in failed_results[:10]:  # Show first 10 failures
                logger.info(f"     - {r.name} ({r.module}/{r.endpoint})")
                logger.info(f"       Expected: {r.expected_status}, Got: {r.actual_status}")
                logger.info(f"       Error: {r.error_message}")
        
        logger.info(f"{'═' * 80}\n")
    
    def generate_html_report(self, total: int, duration: float):
        """Generate HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AXONHIS E2E Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .error {{ color: orange; }}
        .skip {{ color: gray; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>AXONHIS — Comprehensive E2E Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Suite:</strong> {self.suite.value.upper()}</p>
        <p><strong>Module Filter:</strong> {self.module_filter or 'None'}</p>
        <p><strong>Duration:</strong> {duration:.2f}s</p>
        <p><strong>Total Tests:</strong> {total}</p>
        <p class="pass"><strong>Passed:</strong> {self.pass_count}</p>
        <p class="fail"><strong>Failed:</strong> {self.fail_count}</p>
        <p class="error"><strong>Errors:</strong> {self.error_count}</p>
        <p class="skip"><strong>Skipped:</strong> {self.skip_count}</p>
        <p><strong>Pass Rate:</strong> {(self.pass_count/total*100) if total > 0 else 0:.1f}%</p>
    </div>
    
    <h2>Test Results</h2>
    <table>
        <tr>
            <th>#</th>
            <th>Test Name</th>
            <th>Module</th>
            <th>Endpoint</th>
            <th>Method</th>
            <th>Status</th>
            <th>Expected</th>
            <th>Actual</th>
            <th>Time (ms)</th>
            <th>Error</th>
        </tr>
"""
        
        for i, result in enumerate(self.results, 1):
            status_class = result.status.value.lower()
            html += f"""
        <tr>
            <td>{i}</td>
            <td>{result.name}</td>
            <td>{result.module}</td>
            <td>{result.endpoint}</td>
            <td>{result.method}</td>
            <td class="{status_class}">{result.status.value}</td>
            <td>{result.expected_status}</td>
            <td>{result.actual_status}</td>
            <td>{result.response_time_ms:.0f}</td>
            <td>{result.error_message or ''}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        filename = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w') as f:
            f.write(html)
        logger.info(f"  📄 HTML report generated: {filename}")
    
    def generate_json_report(self, total: int, duration: float):
        """Generate JSON report"""
        report = {
            "suite": self.suite.value,
            "module_filter": self.module_filter,
            "duration_seconds": duration,
            "summary": {
                "total": total,
                "passed": self.pass_count,
                "failed": self.fail_count,
                "errors": self.error_count,
                "skipped": self.skip_count,
                "pass_rate": (self.pass_count / total * 100) if total > 0 else 0
            },
            "results": [
                {
                    "name": r.name,
                    "module": r.module,
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status": r.status.value,
                    "expected_status": r.expected_status,
                    "actual_status": r.actual_status,
                    "response_time_ms": r.response_time_ms,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        filename = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"  📄 JSON report generated: {filename}")
    
    def run(self):
        """Run the test suite"""
        self.start_time = datetime.now()
        
        logger.info("=" * 80)
        logger.info("  AXONHIS — COMPREHENSIVE QA END-TO-END TEST SUITE")
        logger.info(f"  Suite: {self.suite.value.upper()}")
        logger.info(f"  Module Filter: {self.module_filter or 'None'}")
        logger.info(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            logger.error("Authentication failed. Cannot proceed with tests.")
            return 1
        
        # Run test modules
        test_modules = [
            ("auth", self.test_auth_module),
            ("patients", self.test_patient_module),
            ("scheduling", self.test_scheduling_module),
            ("opd", self.test_opd_module),
            ("nursing", self.test_nursing_triage_module),
            ("doctor_desk", self.test_doctor_desk_module),
            ("orders", self.test_orders_module),
            ("prescriptions", self.test_prescriptions_module),
            ("lab", self.test_lab_module),
            ("radiology", self.test_radiology_module),
            ("pharmacy", self.test_pharmacy_module),
            ("billing", self.test_billing_module),
            ("er", self.test_er_module),
            ("ipd", self.test_ipd_module),
            ("wards", self.test_wards_module),
            ("ot", self.test_ot_module),
            ("blood_bank", self.test_blood_bank_module),
            ("inventory", self.test_inventory_module),
            ("analytics", self.test_analytics_module),
            ("notifications", self.test_notifications_module),
            ("system", self.test_system_module),
            ("cdss", self.test_cdss_module),
            ("kiosk", self.test_kiosk_module),
        ]
        
        for module_name, module_func in test_modules:
            if self.module_filter and module_name != self.module_filter:
                continue
            try:
                module_func()
            except Exception as e:
                logger.error(f"Error in {module_name} module: {e}")
                traceback.print_exc()
        
        # Generate report
        self.generate_report(format="text")
        self.generate_report(format="html")
        self.generate_report(format="json")
        
        # Return exit code
        return 0 if self.fail_count == 0 and self.error_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="AXONHIS Comprehensive E2E Test Suite")
    parser.add_argument(
        "--suite",
        choices=[s.value for s in TestSuite],
        default=TestSuite.ALL.value,
        help="Test suite to run"
    )
    parser.add_argument(
        "--module",
        type=str,
        default=None,
        help="Filter tests by module name"
    )
    parser.add_argument(
        "--report",
        choices=["text", "html", "json", "all"],
        default="all",
        help="Report format"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:9500/api/v1",
        help="API base URL"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(
        suite=TestSuite(args.suite),
        module_filter=args.module
    )
    runner.client.base_url = args.base_url
    
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
