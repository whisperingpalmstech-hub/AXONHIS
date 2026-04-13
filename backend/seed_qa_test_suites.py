"""Seed QA test suites for each module."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.qa.models import QATestDefinition, QATestSuite
from app.core.qa.schemas import TestDefinitionCreate, TestSuiteCreate
from app.core.qa.services import QAService


async def seed_test_suites():
    """Seed test suites for all modules."""
    async for db in get_db():
        service = QAService(db)
        
        # Create test definitions for Billing module
        billing_tests = []
        
        # Package creation test
        package_creation = await service.create_test_definition(TestDefinitionCreate(
            name="Package Creation Validation",
            description="Validate package creation logic",
            module="billing",
            test_type="logic_check",
            validation_rules={
                "check_type": "package_creation",
                "test_data": {
                    "name": "Test Package",
                    "services": [{"id": "service1", "name": "Consultation"}],
                    "base_price": 1000
                }
            }
        ))
        billing_tests.append(str(package_creation.id))
        
        # Package rate calculation test
        package_rate_calc = await service.create_test_definition(TestDefinitionCreate(
            name="Package Rate Calculation",
            description="Validate package rate calculation",
            module="billing",
            test_type="logic_check",
            validation_rules={
                "check_type": "package_rate_calculation",
                "package_id": "test-package-id",
                "patient_category": "national"
            }
        ))
        billing_tests.append(str(package_rate_calc.id))
        
        # Discount authorization test
        discount_auth = await service.create_test_definition(TestDefinitionCreate(
            name="Discount Authorization",
            description="Validate discount authorization logic",
            module="billing",
            test_type="logic_check",
            validation_rules={
                "check_type": "discount_authorization",
                "discount_percentage": 15,
                "user_role": "billing_executive"
            }
        ))
        billing_tests.append(str(discount_auth.id))
        
        # Create billing test suite
        billing_suite = await service.create_test_suite(TestSuiteCreate(
            name="Billing Module Test Suite",
            description="Comprehensive tests for billing module",
            module="billing",
            test_ids=billing_tests
        ))
        
        # Create test definitions for Stock module
        stock_tests = []
        
        # Stock movement test
        stock_movement = await service.create_test_definition(TestDefinitionCreate(
            name="Stock Movement Validation",
            description="Validate stock movement logic",
            module="stock",
            test_type="logic_check",
            validation_rules={
                "check_type": "stock_movement",
                "transaction_id": "test-transaction-id"
            }
        ))
        stock_tests.append(str(stock_movement.id))
        
        # Stock valuation test
        stock_valuation = await service.create_test_definition(TestDefinitionCreate(
            name="Stock Valuation Validation",
            description="Validate stock valuation logic",
            module="stock",
            test_type="logic_check",
            validation_rules={
                "check_type": "stock_valuation",
                "store_id": "test-store-id",
                "valuation_method": "moving_average"
            }
        ))
        stock_tests.append(str(stock_valuation.id))
        
        # Create stock test suite
        stock_suite = await service.create_test_suite(TestSuiteCreate(
            name="Stock Management Test Suite",
            description="Comprehensive tests for stock management module",
            module="stock",
            test_ids=stock_tests
        ))
        
        # Create test definitions for Database module
        db_tests = []
        
        # Database connection test
        db_connection = await service.create_test_definition(TestDefinitionCreate(
            name="Database Connection Health",
            description="Check database connection health",
            module="database",
            test_type="db_check"
        ))
        db_tests.append(str(db_connection.id))
        
        # Create database test suite
        db_suite = await service.create_test_suite(TestSuiteCreate(
            name="Database Health Test Suite",
            description="Comprehensive tests for database health",
            module="database",
            test_ids=db_tests
        ))
        
        # Create test definitions for API Health module
        api_tests = []
        
        # Health endpoint test
        health_check = await service.create_test_definition(TestDefinitionCreate(
            name="Health Endpoint Check",
            description="Check /health endpoint",
            module="api",
            test_type="health_check",
            endpoint_url="http://localhost:9500/health",
            http_method="GET",
            expected_status=200
        ))
        api_tests.append(str(health_check.id))
        
        # API docs endpoint test
        docs_check = await service.create_test_definition(TestDefinitionCreate(
            name="API Docs Endpoint Check",
            description="Check /docs endpoint",
            module="api",
            test_type="health_check",
            endpoint_url="http://localhost:9500/docs",
            http_method="GET",
            expected_status=200
        ))
        api_tests.append(str(docs_check.id))
        
        # Create API health test suite
        api_suite = await service.create_test_suite(TestSuiteCreate(
            name="API Health Test Suite",
            description="Comprehensive tests for API endpoints health",
            module="api",
            test_ids=api_tests
        ))
        
        print("✅ Test suites seeded successfully:")
        print(f"   - Billing Suite: {billing_suite.id}")
        print(f"   - Stock Suite: {stock_suite.id}")
        print(f"   - Database Suite: {db_suite.id}")
        print(f"   - API Health Suite: {api_suite.id}")
        
        break


if __name__ == "__main__":
    asyncio.run(seed_test_suites())
