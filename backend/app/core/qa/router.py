"""QA Module Router for API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import httpx
import time
import asyncio
import os
import logging

from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Base URL for internal API calls - use localhost within the container
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


def _get_modules_for_app(app: Optional[str] = None) -> Dict[str, list]:
    """Return module endpoints filtered by app name."""
    if app and app in APP_MODULES:
        module_names = APP_MODULES[app]
        return {k: v for k, v in MODULE_ENDPOINTS.items() if k in module_names}
    return MODULE_ENDPOINTS


@router.get("/modules")
async def get_all_modules(app: Optional[str] = None):
    """Get all modules with their endpoint counts. Optionally filter by app."""
    filtered = _get_modules_for_app(app)
    return {
        "modules": [
            {
                "name": module,
                "endpointCount": len(endpoints),
                "endpoints": endpoints
            }
            for module, endpoints in filtered.items()
        ]
    }


@router.get("/modules/{module_name}")
async def get_module_details(module_name: str):
    """Get details for a specific module."""
    endpoints = MODULE_ENDPOINTS.get(module_name)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    return {
        "module": module_name,
        "endpointCount": len(endpoints),
        "endpoints": endpoints
    }


@router.post("/test/module/{module_name}")
async def test_module(module_name: str):
    """Run tests for all endpoints in a specific module."""
    endpoints = MODULE_ENDPOINTS.get(module_name)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    results = []
    passed = 0
    failed = 0
    
    base_url = QA_BASE_URL
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint_info in endpoints:
            endpoint_path = endpoint_info['path']
            methods = endpoint_info['methods']
            
            # Use GET if available, otherwise use the first available method
            method = 'GET' if 'GET' in methods else methods[0] if methods else 'GET'
            
            start_time = time.time()
            status = "failed"
            error_message = None
            status_code = None
            
            try:
                # Make the API call
                if method == 'GET':
                    response = await client.get(f"{base_url}{endpoint_path}")
                elif method == 'POST':
                    response = await client.post(f"{base_url}{endpoint_path}", json={})
                else:
                    response = await client.get(f"{base_url}{endpoint_path}")
                
                status_code = response.status_code
                elapsed_time = (time.time() - start_time) * 1000
                
                # Validate response - anything below 500 is a pass
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
        "module": module_name,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": results
    }


@router.post("/test/all")
async def test_all_modules(app: Optional[str] = None):
    """Run tests for all modules. Optionally filter by app."""
    filtered = _get_modules_for_app(app)
    all_results = {}
    total_passed = 0
    total_failed = 0
    
    for module in filtered.keys():
        try:
            result = await test_module(module)
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
