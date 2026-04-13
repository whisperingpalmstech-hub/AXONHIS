"""QA Module Router for API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import httpx
import time
import asyncio

from app.database import get_db
from app.core.qa.schemas import (
    TestSuiteCreate, TestSuiteResponse,
    TestExecutionRequest, ReportRequest, ReportResponse
)
from app.core.qa.services import QAService

router = APIRouter()

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
}


@router.get("/modules")
async def get_all_modules():
    """Get all modules with their endpoint counts."""
    return {
        "modules": [
            {
                "name": module,
                "endpointCount": len(endpoints),
                "endpoints": endpoints
            }
            for module, endpoints in MODULE_ENDPOINTS.items()
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
async def test_module(module_name: str, db: AsyncSession = Depends(get_db)):
    """Run tests for all endpoints in a specific module."""
    endpoints = MODULE_ENDPOINTS.get(module_name)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    results = []
    passed = 0
    failed = 0
    
    base_url = "http://backend:8000"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint_info in endpoints:
            endpoint_path = endpoint_info['path']
            methods = endpoint_info['methods']
            
            # Use GET if available, otherwise use the first available method
            method = 'GET' if 'GET' in methods else list(methods)[0] if methods else 'GET'
            
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
                
                # Validate response
                if status_code < 500:
                    status = "passed"
                    passed += 1
                else:
                    status = "failed"
                    failed += 1
                    error_message = f"Status code: {status_code}"
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
    
    # Store results in database
    service = QAService(db)
    for result in results:
        await service.create_test_result(
            name=f"{module_name} - {result['endpoint']}",
            module=module_name,
            test_type="api_health",
            status=result['status'],
            execution_time_ms=result['time_ms'],
            error_message=result.get('error')
        )
    
    return {
        "module": module_name,
        "total": len(endpoints),
        "passed": passed,
        "failed": failed,
        "results": results
    }


@router.post("/test/all")
async def test_all_modules(db: AsyncSession = Depends(get_db)):
    """Run tests for all modules."""
    all_results = {}
    total_passed = 0
    total_failed = 0
    
    for module in MODULE_ENDPOINTS.keys():
        try:
            result = await test_module(module, db)
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
        "total_modules": len(MODULE_ENDPOINTS),
        "total_passed": total_passed,
        "total_failed": total_failed
    }


@router.get("/suites", response_model=List[TestSuiteResponse])
async def list_test_suites(
    module: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all test suites."""
    service = QAService(db)
    return await service.get_test_suites(module=module, is_active=is_active)


@router.post("/suites/{suite_id}/run")
async def run_test_suite(
    suite_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Run all tests in a test suite."""
    service = QAService(db)
    return await service.execute_test_suite(suite_id)


@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    report_data: ReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a QA report."""
    service = QAService(db)
    return await service.generate_report(
        suite_id=report_data.suite_id,
        result_ids=report_data.result_ids,
        report_name=report_data.report_name
    )


@router.get("/reports")
async def list_reports(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List QA reports."""
    service = QAService(db)
    return await service.get_reports(limit=limit)
