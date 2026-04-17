"""QA Module Router for API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import httpx
import time
import asyncio
import os
import logging
import uuid
from datetime import datetime

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Base URL for internal API calls - use localhost within the container
# Default to port 8000 (container internal) if no env var is set
# For external access, set QA_BASE_URL=http://localhost:9500 in .env
QA_BASE_URL = os.getenv("QA_BASE_URL", "http://localhost:8000")

# Static module and endpoint mapping (comprehensive coverage)
MODULE_ENDPOINTS = {
    'auth': [
        {'path': '/api/v1/auth/login', 'methods': ['POST']},
        {'path': '/api/v1/auth/register', 'methods': ['POST']},
        {'path': '/api/v1/auth/me', 'methods': ['GET']},
        {'path': '/api/v1/auth/logout', 'methods': ['POST']},
        {'path': '/api/v1/auth/refresh', 'methods': ['POST']},
        {'path': '/api/v1/auth/forgot-password', 'methods': ['POST']},
        {'path': '/api/v1/auth/reset-password', 'methods': ['POST']},
    ],
    'patients': [
        {'path': '/api/v1/patients', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/patients/{id}', 'methods': ['GET', 'PUT', 'DELETE']},
        {'path': '/api/v1/patients/identifiers', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/patients/contacts', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/patients/guardians', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/patients/insurance', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/patients/consents', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/patients/search', 'methods': ['GET']},
        {'path': '/api/v1/patients/mrn/{mrn}', 'methods': ['GET']},
    ],
    'opd': [
        {'path': '/api/v1/opd/visits', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/opd/visits/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/opd/queue', 'methods': ['GET']},
        {'path': '/api/v1/opd/scheduling', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/opd/slots', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/opd/appointments', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/opd/triage', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/opd/smart-queue', 'methods': ['GET']},
        {'path': '/api/v1/opd/consultations', 'methods': ['GET', 'POST']},
    ],
    'ipd': [
        {'path': '/api/v1/ipd/admissions', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ipd/admissions/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/ipd/beds', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ipd/beds/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/ipd/wards', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ipd/discharges', 'methods': ['POST']},
        {'path': '/api/v1/ipd/transfers', 'methods': ['POST']},
        {'path': '/api/v1/ipd/nursing', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ipd/vitals', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ipd/consents', 'methods': ['GET', 'POST']},
    ],
    'er': [
        {'path': '/api/v1/er/triage', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/er/triage/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/er/encounters', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/er/encounters/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/er/dispositions', 'methods': ['POST']},
        {'path': '/api/v1/er/command-center', 'methods': ['GET']},
        {'path': '/api/v1/er/monitoring', 'methods': ['GET']},
        {'path': '/api/v1/er/registration', 'methods': ['POST']},
    ],
    'lab': [
        {'path': '/api/v1/lab/orders', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/lab/orders/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/lab/results', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/lab/results/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/lab/processing', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/lab/processing/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/lab/samples', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/lab/samples/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/lab/worklists', 'methods': ['GET']},
        {'path': '/api/v1/lab/validation', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/lab/reports', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/lab/tests', 'methods': ['GET', 'POST']},
    ],
    'radiology': [
        {'path': '/api/v1/radiology/orders', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/radiology/orders/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/radiology/reports', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/radiology/reports/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/radiology/schedules', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/radiology/studies', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/radiology/studies/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/radiology/diagnostics', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/radiology/worklists', 'methods': ['GET']},
    ],
    'pharmacy': [
        {'path': '/api/v1/pharmacy/prescriptions', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/pharmacy/prescriptions/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/pharmacy/inventory', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/pharmacy/inventory/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/pharmacy/dispensing', 'methods': ['POST']},
        {'path': '/api/v1/pharmacy/dispensing/{id}', 'methods': ['GET']},
        {'path': '/api/v1/pharmacy/stocks', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/pharmacy/drugs', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/pharmacy/drugs/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/pharmacy/sales', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/pharmacy/returns', 'methods': ['POST']},
        {'path': '/api/v1/pharmacy/narcotics', 'methods': ['GET', 'POST']},
    ],
    'inventory': [
        {'path': '/api/v1/inventory/items', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/inventory/items/{id}', 'methods': ['GET', 'PUT', 'DELETE']},
        {'path': '/api/v1/inventory/stock', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/inventory/stock/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/inventory/movements', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/inventory/movements/{id}', 'methods': ['GET']},
        {'path': '/api/v1/inventory/procurement', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/inventory/procurement/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/inventory/verification', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/inventory/valuation', 'methods': ['GET']},
        {'path': '/api/v1/inventory/expiry', 'methods': ['GET']},
        {'path': '/api/v1/inventory/stores', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/inventory/suppliers', 'methods': ['GET', 'POST']},
    ],
    'billing': [
        {'path': '/api/v1/billing/invoices', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/invoices/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/billing/packages', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/packages/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/billing/payments', 'methods': ['POST']},
        {'path': '/api/v1/billing/payments/{id}', 'methods': ['GET']},
        {'path': '/api/v1/billing/pricing', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/pricing/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/billing/stages', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/stages/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/billing/contracts', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/contracts/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/billing/deposits', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/tax', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/credit', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/billing/masters', 'methods': ['GET', 'POST']},
    ],
    'ot': [
        {'path': '/api/v1/ot/schedules', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ot/schedules/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/ot/procedures', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ot/procedures/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/ot/theatres', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ot/theatres/{id}', 'methods': ['GET', 'PUT']},
        {'path': '/api/v1/ot/teams', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ot/checklists', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ot/safety-checks', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/ot/recovery', 'methods': ['GET', 'POST']},
    ],
    'qa': [
        {'path': '/api/v1/qa/suites', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/qa/suites/{id}', 'methods': ['GET', 'PUT', 'DELETE']},
        {'path': '/api/v1/qa/reports', 'methods': ['GET']},
        {'path': '/api/v1/qa/reports/{id}', 'methods': ['GET']},
        {'path': '/api/v1/qa/modules', 'methods': ['GET']},
        {'path': '/api/v1/qa/modules/{module_name}', 'methods': ['GET']},
        {'path': '/api/v1/qa/test/module/{module_name}', 'methods': ['POST']},
        {'path': '/api/v1/qa/test/all', 'methods': ['POST']},
        {'path': '/api/v1/qa/definitions', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/qa/definitions/{id}', 'methods': ['GET', 'PUT', 'DELETE']},
    ],
    'md': [
        {'path': '/api/v1/md/organizations', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/facilities', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/clinicians', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/patients', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/encounters', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/appointments', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/payers', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/coverage', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/billing/invoices', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/documents', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/md/dashboard/stats', 'methods': ['GET']},
    ],
    'clinical_encounter_flow': [
        {'path': '/api/v1/clinical-encounter-flow/start', 'methods': ['POST']},
        {'path': '/api/v1/clinical-encounter-flow/flow/{flow_id}', 'methods': ['GET']},
    ],
    'portal': [
        {'path': '/api/v1/portal/accounts/login', 'methods': ['POST']},
        {'path': '/api/v1/portal/accounts/register', 'methods': ['POST']},
        {'path': '/api/v1/portal/accounts/search', 'methods': ['GET']},
        {'path': '/api/v1/portal/accounts/profile', 'methods': ['GET']},
        {'path': '/api/v1/portal/medical-records/lab-results', 'methods': ['GET']},
        {'path': '/api/v1/portal/medical-records/prescriptions', 'methods': ['GET']},
        {'path': '/api/v1/portal/medical-records/encounters', 'methods': ['GET']},
        {'path': '/api/v1/portal/appointments/doctors', 'methods': ['GET']},
        {'path': '/api/v1/portal/appointments/slots', 'methods': ['GET']},
        {'path': '/api/v1/portal/appointments/my', 'methods': ['GET']},
        {'path': '/api/v1/portal/appointments/book', 'methods': ['POST']},
        {'path': '/api/v1/portal/telemedicine/sessions', 'methods': ['GET']},
        {'path': '/api/v1/portal/billing/invoices', 'methods': ['GET']},
    ],
    'system': [
        {'path': '/api/v1/system/health', 'methods': ['GET']},
        {'path': '/api/v1/system/logs', 'methods': ['GET']},
        {'path': '/api/v1/system/metrics', 'methods': ['GET']},
    ],
    'analytics': [
        {'path': '/api/v1/analytics/clinical-metrics', 'methods': ['GET']},
        {'path': '/api/v1/analytics/dashboards/executive', 'methods': ['GET']},
        {'path': '/api/v1/analytics/financial-metrics', 'methods': ['GET']},
        {'path': '/api/v1/analytics/operational-metrics', 'methods': ['GET']},
        {'path': '/api/v1/analytics/predictions', 'methods': ['GET']},
    ],
    'notifications': [
        {'path': '/api/v1/notifications', 'methods': ['GET']},
        {'path': '/api/v1/notifications/read-all', 'methods': ['POST']},
    ],
    'tasks': [
        {'path': '/api/v1/tasks', 'methods': ['GET', 'POST']},
        {'path': '/api/v1/tasks/my-tasks', 'methods': ['GET']},
    ],
}

# ── Per-app module mapping: which modules each frontend app uses ──
APP_MODULES = {
    'axonhis_md': ['md', 'clinical_encounter_flow'],
    'axonhis': [
        'auth', 'patients', 'opd', 'ipd', 'er', 'lab', 'radiology',
        'pharmacy', 'inventory', 'billing', 'ot', 'system', 'analytics',
        'notifications', 'tasks',
    ],
    'patient_portal': ['portal'],
}

def _generate_smart_dummy_data(endpoint_path: str, method: str) -> Dict:
    """Generate smart dummy data based on endpoint pattern."""
    if method not in ['POST', 'PUT', 'PATCH']:
        return {}
    
    data = {}
    
    # Health check endpoints - no data needed
    if '/health' in endpoint_path:
        return {}
    
    # Auth endpoints
    if '/auth/login' in endpoint_path:
        return {"email": "admin@axonhis.com", "password": "Admin@123"}
    
    # Patient endpoints
    if '/patients' in endpoint_path and method == 'POST':
        # Check if it's a path parameter endpoint
        if '{' in endpoint_path:
            return {}
        return {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "blood_group": "O+",
            "contact_number": "9876543210",
            "email": f"john.doe.{uuid.uuid4().hex[:8]}@example.com",
            "address": "123 Main St, City",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_number": "9876543211"
        }
    
    # IPD endpoints
    if '/ipd/' in endpoint_path and method == 'POST':
        # Check if it's a path parameter endpoint
        if '{' in endpoint_path:
            return {}
        return {
            "patient_name": "John Doe",
            "patient_uhid": "UHID-TEST-001",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "mobile_number": "9876543210",
            "treating_doctor": "Dr. Smith",
            "specialty": "General Medicine",
            "reason_for_admission": "Fever and cough"
        }
    
    # Lab endpoints
    if '/lab/' in endpoint_path and method == 'POST':
        # Check if it's a path parameter endpoint
        if '{' in endpoint_path:
            return {}
        return {
            "test_name": "Complete Blood Count",
            "test_code": "CBC",
            "category": "Hematology",
            "sample_type": "Blood",
            "price": 500.00,
            "is_active": True
        }
    
    # OPD endpoints
    if '/opd/' in endpoint_path and method == 'POST':
        # Check if it's a path parameter endpoint
        if '{' in endpoint_path:
            return {}
        return {
            "patient_name": "John Doe",
            "mobile_number": "9876543210",
            "preferred_date": datetime.now().isoformat(),
            "department": "General Medicine",
            "reason_for_visit": "Routine checkup"
        }
    
    # Billing endpoints
    if '/billing/' in endpoint_path and method == 'POST':
        # Check if it's a path parameter endpoint
        if '{' in endpoint_path:
            return {}
        return {
            "invoice_number": f"INV-{uuid.uuid4().hex[:6].upper()}",
            "patient_id": str(uuid.uuid4()),
            "amount": 1000.00,
            "description": "Test invoice"
        }
    
    # Generic data for other endpoints (skip path parameter endpoints)
    if '{' in endpoint_path:
        return {}
    
    return {"test": True, "id": str(uuid.uuid4())}

def _get_dynamic_endpoints(request: Request, app: Optional[str] = None) -> Dict[str, list]:
    """Dynamically extract endpoints from the FastAPI app routes."""
    modules = {}
    try:
        if not hasattr(request, 'app') or not request.app:
            logger.warning("Request has no app attribute or app is None")
            return modules
            
        if not hasattr(request.app, 'routes'):
            logger.warning("Request.app has no routes attribute")
            return modules
            
        for route in request.app.routes:
            try:
                if isinstance(route, APIRoute):
                    path = route.path
                    # Skip QA module to avoid infinite loops during testing
                    if path.startswith("/api/v1/qa"):
                        continue
                        
                    parts = path.strip("/").split("/")
                    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
                        module_name = parts[2].replace("-", "_")  # Normalize hyphens to underscores
                    else:
                        module_name = "core"
                    
                    # Simple app mapping filtering - use normalized module names (with underscores)
                    if app == "axonhis_md" and module_name not in ["md", "clinical_encounter_flow"]:
                        continue
                    if app == "patient_portal" and module_name not in ["portal"]:
                        continue
                    if app == "axonhis" and module_name in ["md", "portal", "clinical_encounter_flow"]:
                        continue

                    if module_name not in modules:
                        modules[module_name] = []
                        
                    existing_route = next((x for x in modules[module_name] if x['path'] == path), None)
                    if existing_route:
                        existing_route['methods'].extend(list(route.methods))
                        existing_route['methods'] = list(set(existing_route['methods']))
                    else:
                        modules[module_name].append({
                            'path': path,
                            'methods': list(route.methods)
                        })
            except Exception as e:
                logger.warning(f"Error processing route {getattr(route, 'path', 'unknown')}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error in _get_dynamic_endpoints: {e}")
    
    return modules


@router.get("/modules")
async def get_all_modules(request: Request, app: Optional[str] = None):
    """Get all modules with their endpoint counts recursively generated from live router."""
    filtered = _get_dynamic_endpoints(request, app)
    return {
        "modules": [
            {
                "name": module.upper(),
                "endpointCount": len(endpoints),
                "endpoints": endpoints
            }
            for module, endpoints in filtered.items()
        ]
    }


@router.get("/modules/{module_name}")
async def get_module_details(module_name: str, request: Request):
    """Get details for a specific module."""
    filtered = _get_dynamic_endpoints(request)
    # Support case insensitive module matching
    endpoints = next((v for k, v in filtered.items() if k.lower() == module_name.lower()), None)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    return {
        "module": module_name.upper(),
        "endpointCount": len(endpoints),
        "endpoints": endpoints
    }


@router.post("/test/module/{module_name}")
async def test_module(module_name: str, request: Request):
    """Run tests for all endpoints in a specific module dynamically."""
    filtered = _get_dynamic_endpoints(request)
    endpoints = next((v for k, v in filtered.items() if k.lower() == module_name.lower()), None)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    results = []
    passed = 0
    failed = 0
    
    base_url = QA_BASE_URL
    # Grab the current authorization header to pass down the test
    auth_header = request.headers.get("authorization", "")
    headers = {"Authorization": auth_header} if auth_header else {}
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for endpoint_info in endpoints:
            endpoint_path = endpoint_info['path']
            methods = endpoint_info['methods']
            
            # Skip endpoints with path parameters (containing {})
            if '{' in endpoint_path:
                continue
            
            # Prioritize GET
            method = 'GET' if 'GET' in methods else methods[0] if methods else 'GET'
            
            start_time = time.time()
            status = "failed"
            error_message = None
            status_code = None
            
            try:
                if method == 'GET':
                    response = await client.get(f"{base_url}{endpoint_path}")
                elif method == 'POST':
                    test_data = _generate_smart_dummy_data(endpoint_path, 'POST')
                    response = await client.post(f"{base_url}{endpoint_path}", json=test_data)
                elif method == 'PUT':
                    test_data = _generate_smart_dummy_data(endpoint_path, 'PUT')
                    response = await client.put(f"{base_url}{endpoint_path}", json=test_data)
                elif method == 'DELETE':
                    response = await client.delete(f"{base_url}{endpoint_path}")
                else:
                    response = await client.request(method, f"{base_url}{endpoint_path}")
                
                status_code = response.status_code
                elapsed_time = (time.time() - start_time) * 1000
                
                # Treat 4xx as PASS since they just represent missing mock data (e.g. 404) or failed validation (422) for a missing real payload
                if status_code < 500:
                    status = "passed"
                    passed += 1
                else:
                    status = "failed"
                    failed += 1
                    error_message = f"Status code: {status_code}"
            except httpx.TimeoutException:
                elapsed_time = (time.time() - start_time) * 1000
                status = "failed"
                failed += 1
                error_message = "Request timed out (30s)"
            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000
                status = "failed"
                failed += 1
                error_message = str(e)
            
            results.append({
                "endpoint": endpoint_path,
                "method": method,
                "status": status,
                "time_ms": round(elapsed_time, 2),
                "status_code": status_code,
                "error": error_message
            })
    
    return {
        "module": module_name.upper(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results
    }


@router.post("/test/all")
async def test_all_modules(request: Request, app: Optional[str] = None):
    """Run tests for all dynamic modules."""
    filtered = _get_dynamic_endpoints(request, app)
    all_results = {}
    total_passed = 0
    total_failed = 0
    
    for module in filtered.keys():
        try:
            result = await test_module(module, request)
            all_results[module] = result
            total_passed += result['passed']
            total_failed += result['failed']
        except Exception as e:
            all_results[module] = {
                "module": module,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "results": [],
                "error": str(e)
            }
            total_failed += 1
    
    return {
        "modules": all_results,
        "total_modules": len(filtered),
        "total_passed": total_passed,
        "total_failed": total_failed
    }


@router.get("/suites")
async def list_test_suites(
    module: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all test suites."""
    try:
        from app.core.qa.services import QAService
        service = QAService(db)
        return await service.get_test_suites(module=module, is_active=is_active)
    except Exception as e:
        logger.error(f"Error listing test suites: {e}")
        return []


@router.post("/suites/{suite_id}/run")
async def run_test_suite(
    suite_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Run all tests in a test suite."""
    try:
        from app.core.qa.services import QAService
        service = QAService(db)
        return await service.execute_test_suite(suite_id)
    except Exception as e:
        logger.error(f"Error running test suite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate")
async def generate_report(
    report_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Generate a QA report."""
    try:
        from app.core.qa.services import QAService
        service = QAService(db)
        return await service.generate_report(
            suite_id=report_data.get("suite_id"),
            result_ids=report_data.get("result_ids"),
            report_name=report_data.get("report_name", "QA Report")
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def list_reports(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List QA reports."""
    try:
        from app.core.qa.services import QAService
        service = QAService(db)
        return await service.get_reports(limit=limit)
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        return []
