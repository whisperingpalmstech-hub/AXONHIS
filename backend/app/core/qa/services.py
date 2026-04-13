"""QA Module Services for test execution and result aggregation."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.qa.models import (
    QATestDefinition, QATestSuite, QATestResult, QAReport, TestStatus
)
from app.core.qa.schemas import (
    TestDefinitionCreate, TestSuiteCreate, TestExecutionRequest, ReportRequest
)
from app.core.qa.health_checks import (
    check_endpoint_health, check_endpoint_response_time,
    check_endpoint_auth, check_endpoint_data_validation
)
from app.core.qa.db_checks import (
    check_database_connection, check_table_access,
    check_query_performance, check_data_integrity
)
from app.core.qa.logic_checks import (
    check_package_creation, check_package_rate_calculation,
    check_stock_movement, check_stock_valuation,
    check_billing_workflow, check_discount_authorization
)
from app.core.qa.performance_checks import (
    measure_endpoint_performance, measure_query_performance
)
from app.core.qa.pdf_generator import (
    generate_qa_report_pdf, generate_summary_chart_data
)


class QAService:
    """Service for QA test execution and management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_test_definition(
        self, test_data: TestDefinitionCreate
    ) -> QATestDefinition:
        """Create a new test definition."""
        test_def = QATestDefinition(**test_data.model_dump())
        self.db.add(test_def)
        await self.db.commit()
        await self.db.refresh(test_def)
        return test_def
    
    async def get_test_definitions(
        self, module: Optional[str] = None, is_active: Optional[bool] = None
    ) -> List[QATestDefinition]:
        """Get test definitions with optional filters."""
        query = select(QATestDefinition)
        
        if module:
            query = query.where(QATestDefinition.module == module)
        
        if is_active is not None:
            query = query.where(QATestDefinition.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create_test_suite(self, suite_data: TestSuiteCreate) -> QATestSuite:
        """Create a new test suite."""
        suite = QATestSuite(**suite_data.model_dump())
        self.db.add(suite)
        await self.db.commit()
        await self.db.refresh(suite)
        return suite
    
    async def get_test_suites(
        self, module: Optional[str] = None, is_active: Optional[bool] = None
    ) -> List[QATestSuite]:
        """Get test suites with optional filters."""
        query = select(QATestSuite)
        
        if module:
            query = query.where(QATestSuite.module == module)
        
        if is_active is not None:
            query = query.where(QATestSuite.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def execute_test(
        self, test_def: QATestDefinition, performed_by: Optional[str] = None
    ) -> QATestResult:
        """Execute a single test based on its type."""
        result = QATestResult(
            test_definition_id=test_def.id,
            status=TestStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            performed_by=performed_by
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            if test_def.test_type == "health_check":
                health_result = await check_endpoint_health(
                    endpoint_url=test_def.endpoint_url,
                    http_method=test_def.http_method or "GET",
                    expected_status=test_def.expected_status or 200
                )
                
                result.status = TestStatus.PASSED if health_result.is_healthy else TestStatus.FAILED
                result.response_status = health_result.response_status
                result.response_data = {
                    "response_time_ms": health_result.response_time_ms,
                    "is_healthy": health_result.is_healthy
                }
                result.error_message = health_result.error_message
            
            elif test_def.test_type == "db_check":
                db_result = await check_database_connection(self.db)
                
                result.status = TestStatus.PASSED if db_result.connection_healthy else TestStatus.FAILED
                result.response_data = {
                    "connection_healthy": db_result.connection_healthy,
                    "query_time_ms": db_result.query_time_ms
                }
                result.error_message = db_result.error_message
            
            elif test_def.test_type == "logic_check":
                # Logic checks require specific test data
                if test_def.validation_rules:
                    check_type = test_def.validation_rules.get("check_type")
                    
                    if check_type == "package_creation":
                        logic_result = await check_package_creation(
                            test_def.validation_rules.get("test_data", {}),
                            self.db
                        )
                    elif check_type == "package_rate_calculation":
                        logic_result = await check_package_rate_calculation(
                            test_def.validation_rules.get("package_id"),
                            test_def.validation_rules.get("patient_category"),
                            test_def.validation_rules.get("bed_type"),
                            test_def.validation_rules.get("payment_entitlement"),
                            self.db
                        )
                    elif check_type == "stock_movement":
                        logic_result = await check_stock_movement(
                            test_def.validation_rules.get("transaction_id"),
                            self.db
                        )
                    elif check_type == "stock_valuation":
                        logic_result = await check_stock_valuation(
                            test_def.validation_rules.get("store_id"),
                            test_def.validation_rules.get("valuation_method"),
                            self.db
                        )
                    elif check_type == "billing_workflow":
                        logic_result = await check_billing_workflow(
                            test_def.validation_rules.get("bill_id"),
                            test_def.validation_rules.get("workflow_stage"),
                            self.db
                        )
                    else:
                        logic_result = type('obj', (object,), {
                            'status': 'skipped',
                            'result': False,
                            'execution_time_ms': 0,
                            'error_message': f'Unknown check type: {check_type}'
                        })()
                    
                    result.status = TestStatus.PASSED if logic_result.result else TestStatus.FAILED
                    result.response_data = {"check_type": check_type}
                    result.error_message = logic_result.error_message
            
            elif test_def.test_type == "performance_check":
                perf_result = await measure_endpoint_performance(
                    endpoint_url=test_def.endpoint_url,
                    http_method=test_def.http_method or "GET",
                    iterations=test_def.validation_rules.get("iterations", 10) if test_def.validation_rules else 10
                )
                
                result.status = TestStatus.PASSED if perf_result.within_threshold else TestStatus.FAILED
                result.response_data = {
                    "avg_response_time_ms": perf_result.avg_response_time_ms,
                    "min_response_time_ms": perf_result.min_response_time_ms,
                    "max_response_time_ms": perf_result.max_response_time_ms,
                    "within_threshold": perf_result.within_threshold
                }
                result.error_message = perf_result.error_message
            
            else:
                result.status = TestStatus.SKIPPED
                result.error_message = f"Unknown test type: {test_def.test_type}"
        
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.stack_trace = str(e)
        
        completed_at = datetime.now(timezone.utc)
        execution_time_ms = (completed_at - start_time).total_seconds() * 1000
        
        result.completed_at = completed_at
        result.execution_time_ms = execution_time_ms
        
        await self.db.commit()
        await self.db.refresh(result)
        
        return result
    
    async def execute_test_suite(
        self, suite_id: str, performed_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute all tests in a test suite."""
        suite = await self.db.get(QATestSuite, suite_id)
        if not suite:
            raise ValueError(f"Test suite {suite_id} not found")
        
        results = []
        total_time = 0
        
        for test_id in suite.test_ids or []:
            test_def = await self.db.get(QATestDefinition, test_id)
            if test_def and test_def.is_active:
                result = await self.execute_test(test_def, performed_by)
                result.suite_id = suite_id
                results.append({
                    "id": str(result.id),
                    "name": test_def.name,
                    "module": test_def.module,
                    "test_type": test_def.test_type,
                    "status": result.status,
                    "execution_time_ms": result.execution_time_ms,
                    "error_message": result.error_message
                })
                total_time += result.execution_time_ms or 0
        
        return {
            "suite_id": suite_id,
            "suite_name": suite.name,
            "module": suite.module,
            "total_tests": len(results),
            "total_time_ms": total_time,
            "results": results
        }
    
    async def generate_report(
        self, suite_id: Optional[str] = None,
        result_ids: Optional[List[str]] = None,
        report_name: str = "QA Report",
        generated_by: Optional[str] = None
    ) -> QAReport:
        """Generate a QA report from test results."""
        # Get test results
        if result_ids:
            query = select(QATestResult).where(QATestResult.id.in_(result_ids))
        elif suite_id:
            query = select(QATestResult).where(QATestResult.suite_id == suite_id)
        else:
            raise ValueError("Either suite_id or result_ids must be provided")
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        # Calculate summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed_tests = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped_tests = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        error_tests = sum(1 for r in results if r.status == TestStatus.ERROR)
        total_time_ms = sum(r.execution_time_ms or 0 for r in results)
        
        # Prepare test results data
        test_results_data = []
        for r in results:
            test_def = await self.db.get(QATestDefinition, r.test_definition_id)
            test_results_data.append({
                "name": test_def.name if test_def else "Unknown",
                "module": test_def.module if test_def else "unknown",
                "test_type": test_def.test_type if test_def else "unknown",
                "status": r.status,
                "execution_time_ms": r.execution_time_ms or 0,
                "error_message": r.error_message
            })
        
        # Get suite name if provided
        suite_name = "Custom Report"
        if suite_id:
            suite = await self.db.get(QATestSuite, suite_id)
            if suite:
                suite_name = suite.name
        
        # Generate report
        report = QAReport(
            report_name=report_name,
            suite_id=suite_id,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            execution_time_ms=total_time_ms,
            summary=f"{passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100):.1f}%)",
            report_data={
                "test_results": test_results_data,
                "chart_data": generate_summary_chart_data(test_results_data)
            },
            generated_by=generated_by
        )
        
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        
        # Generate PDF
        output_path = f"/tmp/qa_report_{report.id}.pdf"
        try:
            file_path = generate_qa_report_pdf(
                test_results_data,
                suite_name,
                output_path,
                generated_by or "System"
            )
            report.file_path = file_path
            await self.db.commit()
        except Exception as e:
            # If PDF generation fails, still save the report
            report.file_path = None
            await self.db.commit()
        
        return report
    
    async def get_reports(self, limit: int = 100) -> List[QAReport]:
        """Get QA reports."""
        query = select(QAReport).order_by(QAReport.generated_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create_test_result(
        self,
        name: str,
        module: str,
        test_type: str,
        status: str,
        execution_time_ms: float,
        error_message: Optional[str] = None
    ) -> QATestResult:
        """Create a test result directly (for API health checks)."""
        result = QATestResult(
            test_definition_id=None,  # No test definition for API health checks
            status=TestStatus.PASSED if status == "passed" else TestStatus.FAILED if status == "failed" else TestStatus.ERROR,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            error_message=error_message
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result
