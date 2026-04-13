"""QA Module Router for API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import httpx

from app.database import get_db
from app.core.qa.schemas import (
    TestSuiteCreate, TestSuiteResponse,
    TestExecutionRequest, ReportRequest, ReportResponse
)
from app.core.qa.services import QAService

router = APIRouter()

# Module endpoint mapping for health checks
MODULE_ENDPOINTS = {
    'auth': ['/api/v1/auth/login', '/api/v1/auth/register', '/api/v1/auth/me'],
    'patients': ['/api/v1/patients', '/api/v1/patients/identifiers', '/api/v1/patients/contacts'],
    'opd': ['/api/v1/opd/visits', '/api/v1/opd/queue', '/api/v1/opd/scheduling'],
    'ipd': ['/api/v1/ipd/admissions', '/api/v1/ipd/beds', '/api/v1/ipd/discharges'],
    'er': ['/api/v1/er/triage', '/api/v1/er/encounters', '/api/v1/er/dispositions'],
    'lab': ['/api/v1/lab/orders', '/api/v1/lab/results', '/api/v1/lab/processing'],
    'radiology': ['/api/v1/radiology/orders', '/api/v1/radiology/reports'],
    'pharmacy': ['/api/v1/pharmacy/prescriptions', '/api/v1/pharmacy/inventory', '/api/v1/pharmacy/dispensing'],
    'inventory': ['/api/v1/inventory/items', '/api/v1/inventory/stock', '/api/v1/inventory/movements'],
    'billing': ['/api/v1/billing/invoices', '/api/v1/billing/packages', '/api/v1/billing/payments'],
    'ot': ['/api/v1/ot/schedules', '/api/v1/ot/procedures'],
    'qa': ['/api/v1/qa/suites', '/api/v1/qa/reports'],
}


@router.get("/modules/{module_name}/health")
async def check_module_health(
    module_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Check health of all endpoints in a module."""
    if module_name not in MODULE_ENDPOINTS:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    endpoints = MODULE_ENDPOINTS[module_name]
    healthy_count = 0
    total_count = len(endpoints)
    
    # Check each endpoint
    async with httpx.AsyncClient(timeout=5.0) as client:
        for endpoint in endpoints:
            try:
                # Try to ping the endpoint
                response = await client.get(f"http://backend:8000{endpoint}")
                if response.status_code < 500:
                    healthy_count += 1
            except:
                pass
    
    status = 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unknown'
    
    return {
        'status': status,
        'endpointCount': total_count,
        'healthyEndpoints': healthy_count,
        'endpoints': endpoints
    }


@router.post("/modules/{module_name}/run")
async def run_module_tests(
    module_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Run all tests for a specific module."""
    service = QAService(db)
    
    # Get all test suites for this module
    suites = await service.get_test_suites(module=module_name, is_active=True)
    
    if not suites:
        raise HTTPException(status_code=404, detail=f"No active test suites found for module {module_name}")
    
    # Run all suites for this module
    all_results = []
    for suite in suites:
        result = await service.execute_test_suite(suite.id)
        all_results.extend(result.get('results', []))
    
    return {
        'module': module_name,
        'suites_run': len(suites),
        'results': all_results,
        'total_tests': len(all_results),
        'passed': sum(1 for r in all_results if r.get('status') == 'passed'),
        'failed': sum(1 for r in all_results if r.get('status') == 'failed')
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
