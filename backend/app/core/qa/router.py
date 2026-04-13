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
from app.core.qa.endpoint_registry import endpoint_registry

router = APIRouter()


@router.get("/modules")
async def get_all_modules():
    """Get all modules with their endpoint counts."""
    return {
        "modules": [
            {
                "name": module,
                "endpointCount": endpoint_registry.get_endpoint_count(module),
                "endpoints": endpoint_registry.get_module_endpoints(module)
            }
            for module in endpoint_registry.get_modules()
        ]
    }


@router.get("/modules/{module_name}")
async def get_module_details(module_name: str):
    """Get details for a specific module."""
    endpoints = endpoint_registry.get_module_endpoints(module_name)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found or has no endpoints")
    
    return {
        "module": module_name,
        "endpointCount": len(endpoints),
        "endpoints": endpoints
    }


@router.post("/test/module/{module_name}")
async def test_module(module_name: str, db: AsyncSession = Depends(get_db)):
    """Run tests for all endpoints in a specific module."""
    endpoints = endpoint_registry.get_module_endpoints(module_name)
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found or has no endpoints")
    
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
    modules = endpoint_registry.get_modules()
    all_results = {}
    total_passed = 0
    total_failed = 0
    
    for module in modules:
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
        "total_modules": len(modules),
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
