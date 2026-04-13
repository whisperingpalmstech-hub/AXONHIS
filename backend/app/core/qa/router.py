"""QA Module Router for API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.core.qa.schemas import (
    TestSuiteCreate, TestSuiteResponse,
    TestExecutionRequest, ReportRequest, ReportResponse
)
from app.core.qa.services import QAService

router = APIRouter()


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
