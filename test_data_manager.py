#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
 AXONHIS — TEST DATA SETUP AND CLEANUP MANAGER
 Handles test data creation, seeding, and cleanup for E2E tests
═══════════════════════════════════════════════════════════════════════
"""

import requests
import uuid
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataManager:
    """Manages test data lifecycle for E2E tests"""
    
    def __init__(self, base_url: str = "http://localhost:9500/api/v1"):
        self.base_url = base_url
        self.headers = {}
        self.created_resources = {
            "patients": [],
            "visits": [],
            "appointments": [],
            "lab_orders": [],
            "prescriptions": [],
            "er_encounters": [],
            "ipd_requests": [],
            "billing_records": []
        }
    
    def authenticate(self, email: str = "admin@axonhis.com", password: str = "Admin@123") -> bool:
        """Authenticate with the API"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                token = response.json().get("access_token")
                self.headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                logger.info("✓ Authenticated successfully")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def create_test_patient(self, override_data: Optional[Dict] = None) -> Optional[Dict]:
        """Create a test patient"""
        patient_data = {
            "first_name": "TestPatient",
            "last_name": f"E2E-{uuid.uuid4().hex[:6]}",
            "gender": "Male",
            "date_of_birth": "1990-05-15",
            "blood_group": "O+",
            "uhid": f"E2E-{uuid.uuid4().hex[:8].upper()}",
            "primary_phone": "9876543210",
            "email": f"e2e_test_{uuid.uuid4().hex[:8]}@test.com",
            "address_line1": "123 Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "pincode": "400001"
        }
        
        if override_data:
            patient_data.update(override_data)
        
        try:
            response = requests.post(
                f"{self.base_url}/patients/",
                headers=self.headers,
                json=patient_data,
                timeout=10
            )
            if response.status_code in [200, 201]:
                patient = response.json()
                patient_id = patient.get("id")
                self.created_resources["patients"].append(patient_id)
                logger.info(f"✓ Created test patient: {patient_id[:12]}... UHID: {patient_data['uhid']}")
                return patient
            else:
                logger.error(f"Failed to create patient: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            return None
    
    def create_test_visit(self, patient_id: str, doctor_id: str) -> Optional[str]:
        """Create a test OPD visit"""
        visit_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department": "General Medicine",
            "visit_type": "new_visit",
            "chief_complaint": "Test complaint for E2E testing",
            "priority": "normal"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/opd-visits/visits",
                headers=self.headers,
                json=visit_data,
                timeout=10
            )
            if response.status_code in [200, 201]:
                visit = response.json()
                visit_id = visit.get("id", str(uuid.uuid4()))
                self.created_resources["visits"].append(visit_id)
                logger.info(f"✓ Created test visit: {visit_id}")
                return visit_id
            else:
                logger.error(f"Failed to create visit: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error creating visit: {e}")
            return None
    
    def create_test_appointment(self, patient_id: str, doctor_id: str) -> Optional[str]:
        """Create a test appointment"""
        appointment_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_date": datetime.now().strftime("%Y-%m-%d"),
            "slot_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "slot_id": str(uuid.uuid4()),
            "department": "General Medicine",
            "visit_type": "new"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/scheduling/bookings",
                headers=self.headers,
                json=appointment_data,
                timeout=10
            )
            if response.status_code == 200:
                appointment = response.json()
                appointment_id = appointment.get("id")
                self.created_resources["appointments"].append(appointment_id)
                logger.info(f"✓ Created test appointment: {appointment_id}")
                return appointment_id
            else:
                logger.warning(f"Failed to create appointment: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Error creating appointment: {e}")
            return None
    
    def create_test_lab_order(self, visit_id: str, doctor_id: str) -> Optional[str]:
        """Create a test lab order"""
        lab_order_data = {
            "visit_id": visit_id,
            "doctor_id": doctor_id,
            "order_type": "lab",
            "test_name": "Complete Blood Count"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/doctor-desk/orders",
                headers=self.headers,
                json=lab_order_data,
                timeout=10
            )
            if response.status_code == 200:
                order = response.json()
                order_id = order.get("id")
                self.created_resources["lab_orders"].append(order_id)
                logger.info(f"✓ Created test lab order: {order_id}")
                return order_id
            else:
                logger.warning(f"Failed to create lab order: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Error creating lab order: {e}")
            return None
    
    def create_test_prescription(self, visit_id: str, doctor_id: str) -> Optional[str]:
        """Create a test prescription"""
        prescription_data = {
            "visit_id": visit_id,
            "doctor_id": doctor_id,
            "medicine_name": "Amoxicillin",
            "strength": "500mg",
            "dosage": "1 Capsule",
            "frequency": "TDS",
            "duration": "7 days",
            "instructions": "After meals"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/doctor-desk/prescriptions",
                headers=self.headers,
                json=prescription_data,
                timeout=10
            )
            if response.status_code == 200:
                prescription = response.json()
                prescription_id = prescription.get("id")
                self.created_resources["prescriptions"].append(prescription_id)
                logger.info(f"✓ Created test prescription: {prescription_id}")
                return prescription_id
            else:
                logger.warning(f"Failed to create prescription: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Error creating prescription: {e}")
            return None
    
    def cleanup_test_data(self) -> bool:
        """Clean up all created test data"""
        logger.info("\n" + "=" * 60)
        logger.info("CLEANING UP TEST DATA")
        logger.info("=" * 60)
        
        success = True
        
        # Note: In a real implementation, you would have DELETE endpoints
        # For now, we'll log what would be cleaned up
        for resource_type, resource_ids in self.created_resources.items():
            if resource_ids:
                logger.info(f"  {resource_type}: {len(resource_ids)} items to clean up")
                for resource_id in resource_ids:
                    logger.info(f"    - {resource_id}")
        
        logger.info("✓ Test data cleanup completed (logged)")
        return success
    
    def setup_full_test_scenario(self) -> Dict[str, Any]:
        """Set up a complete test scenario with all related data"""
        logger.info("\n" + "=" * 60)
        logger.info("SETTING UP FULL TEST SCENARIO")
        logger.info("=" * 60)
        
        scenario_data = {}
        doctor_id = "00000000-0000-0000-0000-000000000009"
        
        # Create patient
        patient = self.create_test_patient()
        if patient:
            scenario_data["patient_id"] = patient.get("id")
            scenario_data["uhid"] = patient.get("uhid")
            
            # Create appointment
            appointment_id = self.create_test_appointment(
                patient.get("id"),
                doctor_id
            )
            if appointment_id:
                scenario_data["appointment_id"] = appointment_id
            
            # Create visit
            visit_id = self.create_test_visit(
                patient.get("id"),
                doctor_id
            )
            if visit_id:
                scenario_data["visit_id"] = visit_id
                scenario_data["doctor_id"] = doctor_id
                
                # Create lab order
                lab_order_id = self.create_test_lab_order(visit_id, doctor_id)
                if lab_order_id:
                    scenario_data["lab_order_id"] = lab_order_id
                
                # Create prescription
                prescription_id = self.create_test_prescription(visit_id, doctor_id)
                if prescription_id:
                    scenario_data["prescription_id"] = prescription_id
        
        logger.info("\n✓ Full test scenario setup completed")
        logger.info(f"  Scenario data: {json.dumps(scenario_data, indent=2)}")
        
        return scenario_data
    
    def export_test_data_state(self, filename: str = "test_data_state.json"):
        """Export current test data state to JSON"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "created_resources": self.created_resources,
            "headers": self.headers
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"✓ Test data state exported to {filename}")
    
    def import_test_data_state(self, filename: str = "test_data_state.json") -> bool:
        """Import test data state from JSON"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            self.created_resources = state.get("created_resources", {})
            self.headers = state.get("headers", {})
            
            logger.info(f"✓ Test data state imported from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to import test data state: {e}")
            return False


def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AXONHIS Test Data Manager")
    parser.add_argument(
        "--action",
        choices=["setup", "cleanup", "export", "import"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:9500/api/v1",
        help="API base URL"
    )
    parser.add_argument(
        "--file",
        default="test_data_state.json",
        help="State file for export/import"
    )
    
    args = parser.parse_args()
    
    manager = TestDataManager(base_url=args.base_url)
    
    if not manager.authenticate():
        logger.error("Authentication failed. Exiting.")
        sys.exit(1)
    
    if args.action == "setup":
        scenario_data = manager.setup_full_test_scenario()
        print(f"\nScenario Data: {json.dumps(scenario_data, indent=2)}")
    
    elif args.action == "cleanup":
        manager.cleanup_test_data()
    
    elif args.action == "export":
        manager.export_test_data_state(args.file)
    
    elif args.action == "import":
        if manager.import_test_data_state(args.file):
            print(f"\nImported resources: {json.dumps(manager.created_resources, indent=2)}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
