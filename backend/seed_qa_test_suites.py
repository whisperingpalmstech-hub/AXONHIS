"""Seed QA test suites for each module."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.qa.models import QATestDefinition, QATestSuite
from app.core.qa.schemas import TestDefinitionCreate, TestSuiteCreate
from app.core.qa.services import QAService


async def seed_test_suites():
    """Seed comprehensive test suites for all modules."""
    async for db in get_db():
        service = QAService(db)
        
        base_url = "http://localhost:9500/api/v1"
        
        # Core Platform & Auth Module Tests
        core_tests = []
        
        core_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="ABDM Health Check",
            description="Check ABDM module endpoint",
            module="abdm",
            test_type="health_check",
            endpoint_url=f"{base_url}",
            http_method="GET",
            expected_status=200
        ))).id))
        
        core_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Auth Module Health",
            description="Check auth module endpoint",
            module="auth",
            test_type="health_check",
            endpoint_url=f"{base_url}/auth",
            http_method="GET",
            expected_status=200
        ))).id))
        
        core_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Audit Module Health",
            description="Check audit module endpoint",
            module="audit",
            test_type="health_check",
            endpoint_url=f"{base_url}/audit",
            http_method="GET",
            expected_status=200
        ))).id))
        
        core_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Files Module Health",
            description="Check files module endpoint",
            module="files",
            test_type="health_check",
            endpoint_url=f"{base_url}/files",
            http_method="GET",
            expected_status=200
        ))).id))
        
        core_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Notifications Module Health",
            description="Check notifications module endpoint",
            module="notifications",
            test_type="health_check",
            endpoint_url=f"{base_url}/notifications",
            http_method="GET",
            expected_status=200
        ))).id))
        
        core_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Config Module Health",
            description="Check config module endpoint",
            module="config",
            test_type="health_check",
            endpoint_url=f"{base_url}/config",
            http_method="GET",
            expected_status=200
        ))).id))
        
        core_suite = await service.create_test_suite(TestSuiteCreate(
            name="Core Platform Test Suite",
            description="Comprehensive tests for core platform modules",
            module="core",
            test_ids=core_tests
        ))
        
        # Clinical Module Tests
        clinical_tests = []
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Patients Module Health",
            description="Check patients module endpoint",
            module="patients",
            test_type="health_check",
            endpoint_url=f"{base_url}/patients",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Encounters Module Health",
            description="Check encounters module endpoint",
            module="encounters",
            test_type="health_check",
            endpoint_url=f"{base_url}/encounters",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Orders Module Health",
            description="Check orders module endpoint",
            module="orders",
            test_type="health_check",
            endpoint_url=f"{base_url}/orders",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Tasks Module Health",
            description="Check tasks module endpoint",
            module="tasks",
            test_type="health_check",
            endpoint_url=f"{base_url}/tasks",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Lab Module Health",
            description="Check lab module endpoint",
            module="lab",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Pharmacy Module Health",
            description="Check pharmacy module endpoint",
            module="pharmacy",
            test_type="health_check",
            endpoint_url=f"{base_url}/pharmacy",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="AI Module Health",
            description="Check AI module endpoint",
            module="ai",
            test_type="health_check",
            endpoint_url=f"{base_url}/ai",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Analytics Module Health",
            description="Check analytics module endpoint",
            module="analytics",
            test_type="health_check",
            endpoint_url=f"{base_url}/analytics",
            http_method="GET",
            expected_status=200
        ))).id))
        
        clinical_suite = await service.create_test_suite(TestSuiteCreate(
            name="Clinical Modules Test Suite",
            description="Comprehensive tests for clinical modules",
            module="clinical",
            test_ids=clinical_tests
        ))
        
        # Billing Module Tests (Enhanced)
        billing_tests = []
        
        # New billing modules
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Package Management Health",
            description="Check package management endpoint",
            module="billing_packages",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/packages",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Multi-stage Billing Health",
            description="Check multi-stage billing endpoint",
            module="billing_stages",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/stages",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Variable Pricing Health",
            description="Check variable pricing endpoint",
            module="billing_pricing",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/pricing",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Contract Management Health",
            description="Check contract management endpoint",
            module="billing_contracts",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/contracts",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Deposit Management Health",
            description="Check deposit management endpoint",
            module="billing_deposits",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/deposits",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Taxation Module Health",
            description="Check taxation endpoint",
            module="billing_tax",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/tax",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Credit Billing Health",
            description="Check credit billing endpoint",
            module="billing_credit",
            test_type="health_check",
            endpoint_url=f"{base_url}/billing/credit",
            http_method="GET",
            expected_status=200
        ))).id))
        
        billing_suite = await service.create_test_suite(TestSuiteCreate(
            name="Billing Module Test Suite",
            description="Comprehensive tests for billing module",
            module="billing",
            test_ids=billing_tests
        ))
        
        # Stock Management Module Tests (Enhanced)
        stock_tests = []
        
        stock_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Inventory Module Health",
            description="Check inventory module endpoint",
            module="inventory",
            test_type="health_check",
            endpoint_url=f"{base_url}/inventory",
            http_method="GET",
            expected_status=200
        ))).id))
        
        stock_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Stock Movement Health",
            description="Check stock movement endpoint",
            module="stock_movement",
            test_type="health_check",
            endpoint_url=f"{base_url}/inventory/movement",
            http_method="GET",
            expected_status=200
        ))).id))
        
        stock_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Expiry Management Health",
            description="Check expiry management endpoint",
            module="stock_expiry",
            test_type="health_check",
            endpoint_url=f"{base_url}/inventory/expiry",
            http_method="GET",
            expected_status=200
        ))).id))
        
        stock_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Stock Valuation Health",
            description="Check stock valuation endpoint",
            module="stock_valuation",
            test_type="health_check",
            endpoint_url=f"{base_url}/inventory/valuation",
            http_method="GET",
            expected_status=200
        ))).id))
        
        stock_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Stock Verification Health",
            description="Check stock verification endpoint",
            module="stock_verification",
            test_type="health_check",
            endpoint_url=f"{base_url}/inventory/verification",
            http_method="GET",
            expected_status=200
        ))).id))
        
        stock_suite = await service.create_test_suite(TestSuiteCreate(
            name="Stock Management Test Suite",
            description="Comprehensive tests for stock management module",
            module="stock",
            test_ids=stock_tests
        ))
        
        # Department Module Tests
        department_tests = []
        
        department_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Blood Bank Health",
            description="Check blood bank endpoint",
            module="blood_bank",
            test_type="health_check",
            endpoint_url=f"{base_url}/blood_bank",
            http_method="GET",
            expected_status=200
        ))).id))
        
        department_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Wards Module Health",
            description="Check wards module endpoint",
            module="wards",
            test_type="health_check",
            endpoint_url=f"{base_url}/wards",
            http_method="GET",
            expected_status=200
        ))).id))
        
        department_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Radiology Health",
            description="Check radiology endpoint",
            module="radiology",
            test_type="health_check",
            endpoint_url=f"{base_url}/radiology",
            http_method="GET",
            expected_status=200
        ))).id))
        
        department_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="OT Module Health",
            description="Check OT module endpoint",
            module="ot",
            test_type="health_check",
            endpoint_url=f"{base_url}/ot",
            http_method="GET",
            expected_status=200
        ))).id))
        
        department_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Linen Module Health",
            description="Check linen module endpoint",
            module="linen",
            test_type="health_check",
            endpoint_url=f"{base_url}/linen",
            http_method="GET",
            expected_status=200
        ))).id))
        
        department_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="CSSD Module Health",
            description="Check CSSD module endpoint",
            module="cssd",
            test_type="health_check",
            endpoint_url=f"{base_url}/cssd",
            http_method="GET",
            expected_status=200
        ))).id))
        
        department_suite = await service.create_test_suite(TestSuiteCreate(
            name="Department Modules Test Suite",
            description="Comprehensive tests for department modules",
            module="departments",
            test_ids=department_tests
        ))
        
        # System Module Tests
        system_tests = []
        
        system_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="System Health Check",
            description="Check system health endpoint",
            module="system",
            test_type="health_check",
            endpoint_url=f"{base_url}/system",
            http_method="GET",
            expected_status=200
        ))).id))
        
        system_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="System Logging Health",
            description="Check system logging endpoint",
            module="system",
            test_type="health_check",
            endpoint_url=f"{base_url}/system/logs",
            http_method="GET",
            expected_status=200
        ))).id))
        
        system_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="System Monitoring Health",
            description="Check system monitoring endpoint",
            module="system",
            test_type="health_check",
            endpoint_url=f"{base_url}/system/monitoring",
            http_method="GET",
            expected_status=200
        ))).id))
        
        system_suite = await service.create_test_suite(TestSuiteCreate(
            name="System Module Test Suite",
            description="Comprehensive tests for system modules",
            module="system",
            test_ids=system_tests
        ))
        
        # LIS Module Tests
        lis_tests = []
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Test Order Health",
            description="Check LIS test order endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/test_order",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Phlebotomy Health",
            description="Check LIS phlebotomy endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/phlebotomy",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Central Receiving Health",
            description="Check LIS central receiving endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/central_receiving",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Processing Health",
            description="Check LIS processing endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/processing",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Analyzer Health",
            description="Check LIS analyzer endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/analyzer",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Validation Health",
            description="Check LIS validation endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/validation",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="LIS Reporting Health",
            description="Check LIS reporting endpoint",
            module="lis",
            test_type="health_check",
            endpoint_url=f"{base_url}/lab/reporting",
            http_method="GET",
            expected_status=200
        ))).id))
        
        lis_suite = await service.create_test_suite(TestSuiteCreate(
            name="LIS Module Test Suite",
            description="Comprehensive tests for LIS module",
            module="lis",
            test_ids=lis_tests
        ))
        
        # Additional Module Tests
        additional_tests = []
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Scheduling Module Health",
            description="Check scheduling endpoint",
            module="scheduling",
            test_type="health_check",
            endpoint_url=f"{base_url}/scheduling",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="OPD Visits Health",
            description="Check OPD visits endpoint",
            module="opd_visits",
            test_type="health_check",
            endpoint_url=f"{base_url}/opd_visits",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Smart Queue Health",
            description="Check smart queue endpoint",
            module="smart_queue",
            test_type="health_check",
            endpoint_url=f"{base_url}/smart_queue",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Nursing Triage Health",
            description="Check nursing triage endpoint",
            module="nursing_triage",
            test_type="health_check",
            endpoint_url=f"{base_url}/nursing_triage",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Doctor Desk Health",
            description="Check doctor desk endpoint",
            module="doctor_desk",
            test_type="health_check",
            endpoint_url=f"{base_url}/doctor_desk",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="RCM Billing Health",
            description="Check RCM billing endpoint",
            module="rcm_billing",
            test_type="health_check",
            endpoint_url=f"{base_url}/rcm_billing",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="IPD Module Health",
            description="Check IPD module endpoint",
            module="ipd",
            test_type="health_check",
            endpoint_url=f"{base_url}/ipd",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="ER Module Health",
            description="Check ER module endpoint",
            module="er",
            test_type="health_check",
            endpoint_url=f"{base_url}/er",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Integration Module Health",
            description="Check integration endpoint",
            module="integration",
            test_type="health_check",
            endpoint_url=f"{base_url}/integration",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="AxonHIS MD Health",
            description="Check AxonHIS MD endpoint",
            module="axonhis_md",
            test_type="health_check",
            endpoint_url=f"{base_url}/axonhis_md",
            http_method="GET",
            expected_status=200
        ))).id))
        
        additional_suite = await service.create_test_suite(TestSuiteCreate(
            name="Additional Modules Test Suite",
            description="Comprehensive tests for additional modules",
            module="additional",
            test_ids=additional_tests
        ))
        
        # Database Health Tests
        db_tests = []
        
        db_tests.append(str((await service.create_test_definition(TestDefinitionCreate(
            name="Database Connection Health",
            description="Check database connection health",
            module="database",
            test_type="db_check"
        ))).id))
        
        db_suite = await service.create_test_suite(TestSuiteCreate(
            name="Database Health Test Suite",
            description="Comprehensive tests for database health",
            module="database",
            test_ids=db_tests
        ))
        
        print("✅ Comprehensive test suites seeded successfully:")
        print(f"   - Core Platform Suite: {core_suite.id}")
        print(f"   - Clinical Modules Suite: {clinical_suite.id}")
        print(f"   - Billing Module Suite: {billing_suite.id}")
        print(f"   - Stock Management Suite: {stock_suite.id}")
        print(f"   - Department Modules Suite: {department_suite.id}")
        print(f"   - System Module Suite: {system_suite.id}")
        print(f"   - LIS Module Suite: {lis_suite.id}")
        print(f"   - Additional Modules Suite: {additional_suite.id}")
        print(f"   - Database Health Suite: {db_suite.id}")
        
        break


if __name__ == "__main__":
    asyncio.run(seed_test_suites())
