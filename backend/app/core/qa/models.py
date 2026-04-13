"""QA Module Models for test definitions and results."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid
from enum import Enum

from app.database import Base


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


class QATestDefinition(Base):
    """Defines a test to be executed."""
    __tablename__ = "qa_test_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    module = Column(String(100), nullable=False, index=True)  # e.g., 'billing', 'stock', 'pharmacy'
    test_type = Column(String(50), nullable=False)  # TestType enum
    endpoint_url = Column(String(500), nullable=True)  # For health checks
    http_method = Column(String(10), nullable=True)  # GET, POST, etc.
    expected_status = Column(Integer, nullable=True)  # Expected HTTP status
    max_response_time_ms = Column(Integer, nullable=True)  # For performance checks
    validation_rules = Column(JSONB, nullable=True)  # JSON validation rules
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class QATestSuite(Base):
    """Groups tests into suites for execution."""
    __tablename__ = "qa_test_suites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    module = Column(String(100), nullable=False, index=True)
    test_ids = Column(JSONB, nullable=True)  # List of test definition IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class QATestResult(Base):
    """Stores test execution results."""
    __tablename__ = "qa_test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_definition_id = Column(UUID(as_uuid=True), ForeignKey("qa_test_definitions.id", ondelete="CASCADE"), nullable=True, index=True)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("qa_test_suites.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default=TestStatus.PENDING)
    execution_time_ms = Column(Numeric(10, 2), nullable=True)
    response_status = Column(Integer, nullable=True)
    response_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class QAReport(Base):
    """Stores generated QA reports."""
    __tablename__ = "qa_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_name = Column(String(200), nullable=False)
    suite_id = Column(UUID(as_uuid=True), ForeignKey("qa_test_suites.id", ondelete="CASCADE"), nullable=True)
    total_tests = Column(Integer, nullable=False, default=0)
    passed_tests = Column(Integer, nullable=False, default=0)
    failed_tests = Column(Integer, nullable=False, default=0)
    skipped_tests = Column(Integer, nullable=False, default=0)
    error_tests = Column(Integer, nullable=False, default=0)
    execution_time_ms = Column(Numeric(12, 2), nullable=True)
    summary = Column(Text, nullable=True)
    report_data = Column(JSONB, nullable=True)  # Detailed report data
    file_path = Column(String(500), nullable=True)  # PDF file path
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
