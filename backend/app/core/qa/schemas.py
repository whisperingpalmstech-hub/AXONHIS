"""QA Module Schemas for request/response validation."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(str, Enum):
    """Type of test check."""
    HEALTH_CHECK = "health_check"
    DB_CHECK = "db_check"
    LOGIC_CHECK = "logic_check"
    PERFORMANCE_CHECK = "performance_check"


class TestDefinitionBase(BaseModel):
    """Base schema for test definition."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    module: str = Field(..., max_length=100)
    test_type: TestType
    endpoint_url: Optional[str] = None
    http_method: Optional[str] = None
    expected_status: Optional[int] = None
    max_response_time_ms: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: bool = True


class TestDefinitionCreate(TestDefinitionBase):
    """Schema for creating a test definition."""
    pass


class TestDefinitionUpdate(BaseModel):
    """Schema for updating a test definition."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    module: Optional[str] = Field(None, max_length=100)
    test_type: Optional[TestType] = None
    endpoint_url: Optional[str] = None
    http_method: Optional[str] = None
    expected_status: Optional[int] = None
    max_response_time_ms: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TestDefinitionResponse(TestDefinitionBase):
    """Schema for test definition response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestSuiteBase(BaseModel):
    """Base schema for test suite."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    module: str = Field(..., max_length=100)
    test_ids: Optional[List[str]] = None
    is_active: bool = True


class TestSuiteCreate(TestSuiteBase):
    """Schema for creating a test suite."""
    pass


class TestSuiteUpdate(BaseModel):
    """Schema for updating a test suite."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    module: Optional[str] = Field(None, max_length=100)
    test_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TestSuiteResponse(TestSuiteBase):
    """Schema for test suite response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestResultBase(BaseModel):
    """Base schema for test result."""
    test_definition_id: str
    suite_id: Optional[str] = None
    status: TestStatus = TestStatus.PENDING
    execution_time_ms: Optional[float] = None
    response_status: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


class TestResultResponse(TestResultBase):
    """Schema for test result response."""
    id: str
    performed_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestExecutionRequest(BaseModel):
    """Schema for test execution request."""
    suite_id: Optional[str] = None
    test_ids: Optional[List[str]] = None


class TestExecutionResponse(BaseModel):
    """Schema for test execution response."""
    execution_id: str
    status: str
    total_tests: int
    completed_tests: int
    results: List[TestResultResponse]


class ReportRequest(BaseModel):
    """Schema for report generation request."""
    suite_id: Optional[str] = None
    result_ids: Optional[List[str]] = None
    report_name: str = Field(..., max_length=200)


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: str
    report_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    execution_time_ms: Optional[float] = None
    summary: Optional[str] = None
    file_path: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class HealthCheckRequest(BaseModel):
    """Schema for health check request."""
    endpoint_url: str
    http_method: str = "GET"
    expected_status: int = 200
    auth_token: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    endpoint_url: str
    status: str
    response_status: Optional[int] = None
    response_time_ms: float
    is_healthy: bool
    error_message: Optional[str] = None


class DBCheckRequest(BaseModel):
    """Schema for database check request."""
    table_name: Optional[str] = None
    query: Optional[str] = None
    max_time_ms: Optional[int] = None


class DBCheckResponse(BaseModel):
    """Schema for database check response."""
    status: str
    connection_healthy: bool
    table_accessible: Optional[bool] = None
    query_time_ms: Optional[float] = None
    data_integrity_healthy: Optional[bool] = None
    error_message: Optional[str] = None


class LogicCheckRequest(BaseModel):
    """Schema for logic check request."""
    check_type: str
    test_data: Dict[str, Any]


class LogicCheckResponse(BaseModel):
    """Schema for logic check response."""
    status: str
    check_type: str
    result: bool
    execution_time_ms: float
    error_message: Optional[str] = None


class PerformanceCheckRequest(BaseModel):
    """Schema for performance check request."""
    endpoint_url: str
    max_time_ms: Optional[int] = None
    iterations: int = 10


class PerformanceCheckResponse(BaseModel):
    """Schema for performance check response."""
    endpoint_url: str
    status: str
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    within_threshold: bool
    error_message: Optional[str] = None
