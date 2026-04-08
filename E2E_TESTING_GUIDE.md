# AXONHIS End-to-End Testing Guide

## Overview

This guide provides comprehensive instructions for running end-to-end tests on the AXONHIS platform like a professional QA engineer.

## Test Suite Components

### 1. Comprehensive E2E Test Suite (`comprehensive_e2e_test_suite.py`)

A professional-grade testing framework that systematically tests all API endpoints across all modules.

**Features:**
- Systematic endpoint testing across 23+ modules
- Test data factories for realistic test data
- Positive and negative test cases
- Detailed HTML, JSON, and text reports
- Test categorization (smoke, regression, integration, performance, security)
- Performance metrics (response times)
- Retry logic for flaky tests
- Authentication/authorization testing
- Data validation testing
- Error handling validation

### 2. Test Data Manager (`test_data_manager.py`)

Handles test data lifecycle including creation, seeding, and cleanup.

**Features:**
- Automated test data creation
- Full test scenario setup
- Test data state export/import
- Cleanup utilities

## Prerequisites

1. **Docker and Docker Compose** installed
2. **AXONHIS platform running** on localhost:9500
3. **Python 3.8+** with required packages:
   ```bash
   pip install requests
   ```

## Starting the Test Environment

### Option 1: Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Option 2: Manual Backend Start

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Running Tests

### Basic Usage

Run the complete test suite:
```bash
python comprehensive_e2e_test_suite.py
```

### Test Suite Options

#### Run Specific Test Suite

```bash
# Smoke tests (critical path only)
python comprehensive_e2e_test_suite.py --suite smoke

# Regression tests (full suite)
python comprehensive_e2e_test_suite.py --suite regression

# Integration tests (cross-module)
python comprehensive_e2e_test_suite.py --suite integration

# Performance tests
python comprehensive_e2e_test_suite.py --suite performance

# Security tests
python comprehensive_e2e_test_suite.py --suite security
```

#### Run Tests for Specific Module

```bash
# Test only authentication module
python comprehensive_e2e_test_suite.py --module auth

# Test only patient module
python comprehensive_e2e_test_suite.py --module patients

# Test only lab module
python comprehensive_e2e_test_suite.py --module lab

# Test only doctor desk module
python comprehensive_e2e_test_suite.py --module doctor_desk
```

#### Available Modules

- `auth` - Authentication
- `patients` - Patient Management
- `scheduling` - Scheduling & Appointments
- `opd` - OPD Workflow
- `nursing` - Nursing Triage
- `doctor_desk` - Doctor Desk / EMR
- `orders` - CPOE Orders
- `prescriptions` - Prescriptions
- `lab` - Laboratory (LIS)
- `radiology` - Radiology (RIS)
- `pharmacy` - Pharmacy
- `billing` - Billing & RCM
- `er` - Emergency Room
- `ipd` - Inpatient Department
- `wards` - Ward Management
- `ot` - Operating Theatre
- `blood_bank` - Blood Bank
- `inventory` - Inventory & Stores
- `analytics` - Analytics & BI
- `notifications` - Notifications
- `system` - System Health
- `cdss` - Clinical Decision Support
- `kiosk` - Self-Service Kiosk

#### Custom API URL

```bash
python comprehensive_e2e_test_suite.py --base-url http://your-api-url:port/api/v1
```

#### Report Format Options

```bash
# Generate all reports (default)
python comprehensive_e2e_test_suite.py --report all

# Generate only text report
python comprehensive_e2e_test_suite.py --report text

# Generate only HTML report
python comprehensive_e2e_test_suite.py --report html

# Generate only JSON report
python comprehensive_e2e_test_suite.py --report json
```

## Test Data Management

### Setup Test Data

```bash
# Set up a complete test scenario
python test_data_manager.py --action setup

# This will create:
# - Test patient
# - Test appointment
# - Test visit
# - Test lab orders
# - Test prescriptions
```

### Cleanup Test Data

```bash
# Clean up all created test data
python test_data_manager.py --action cleanup
```

### Export/Import Test Data State

```bash
# Export current test data state
python test_data_manager.py --action export --file my_test_state.json

# Import test data state
python test_data_manager.py --action import --file my_test_state.json
```

## Understanding Test Results

### Console Output

```
═══════════════════════════════════════════════════════════════════════
  AXONHIS — COMPREHENSIVE QA END-TO-END TEST SUITE
  Suite: ALL
  Module Filter: None
  Started: 2026-04-08 14:30:00
═══════════════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────────────────
  📋 AUTHENTICATION & SYSTEM HEALTH
────────────────────────────────────────────────────────────────────────
  [001] ✅ PASS: Health Check (200) - 45ms
  [002] ✅ PASS: Login (Admin) (200) - 120ms
  ✓ Authenticated successfully
```

### Report Files

After test execution, three report files are generated:

1. **Text Report** (console output)
2. **HTML Report** (`e2e_test_report_YYYYMMDD_HHMMSS.html`)
   - Interactive HTML report with all test results
   - Color-coded status indicators
   - Sortable table
   - Performance metrics

3. **JSON Report** (`e2e_test_report_YYYYMMDD_HHMMSS.json`)
   - Machine-readable format
   - Suitable for CI/CD integration
   - Contains all test details

### Test Status Indicators

- ✅ **PASS** - Test passed successfully
- ❌ **FAIL** - Test failed (unexpected response)
- 🚨 **ERROR** - Test encountered an exception
- ⚠️ **SKIP** - Test skipped (suite filter or condition)

### Metrics

- **Pass Rate** - Percentage of passed tests
- **Average Response Time** - Mean response time across all passed tests
- **Duration** - Total test execution time

## Test Categories

### Smoke Tests
Critical path tests that validate the core functionality:
- Health check
- Authentication
- Patient registration
- Basic OPD workflow
- System health endpoints

### Regression Tests
Full test suite covering all modules to detect regressions.

### Integration Tests
Cross-module integration tests validating data flow between modules.

### Performance Tests
Tests that measure response times and identify performance bottlenecks.

### Security Tests
Tests that validate:
- Authentication/authorization
- Input validation
- Error handling
- Data protection

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: axonhis_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install requests
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for backend
        run: |
          timeout 60 bash -c 'until curl -s http://localhost:9500/health; do sleep 2; done'
      
      - name: Run smoke tests
        run: python comprehensive_e2e_test_suite.py --suite smoke
      
      - name: Run full regression
        run: python comprehensive_e2e_test_suite.py --suite regression
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: e2e_test_report_*.html
```

## Troubleshooting

### Backend Not Responding

```bash
# Check if backend is running
curl http://localhost:9500/health

# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Authentication Failures

```bash
# Verify admin credentials in .env file
# Default: admin@axonhis.com / Admin@123

# Check database connection
docker-compose logs postgres
```

### Timeouts

```bash
# Increase timeout in test script
# Modify the timeout parameter in APIClient.__init__
python comprehensive_e2e_test_suite.py --base-url http://localhost:9500/api/v1
```

### Module-Specific Failures

```bash
# Run only the failing module to debug
python comprehensive_e2e_test_suite.py --module <module_name>

# Check logs for specific errors
tail -f e2e_test_results.log
```

## Best Practices

1. **Run smoke tests before full regression** - Quick validation of critical paths
2. **Use module filters for debugging** - Isolate specific modules
3. **Review HTML reports** - Get detailed insights into failures
4. **Clean up test data regularly** - Avoid database bloat
5. **Integrate with CI/CD** - Automate test execution
6. **Monitor performance metrics** - Track response times over time
7. **Keep test data realistic** - Use test data factories
8. **Test negative scenarios** - Validate error handling

## Test Coverage

The comprehensive test suite covers:

- **23+ modules** across the entire platform
- **100+ API endpoints** with various HTTP methods
- **Authentication & authorization** flows
- **Patient lifecycle** management
- **Clinical workflows** (OPD, IPD, ER, OT)
- **Ancillary services** (Lab, Radiology, Pharmacy)
- **Administrative functions** (Billing, Inventory, Analytics)
- **System operations** (Health, Audit, Notifications)

## Extending the Test Suite

### Adding New Test Cases

```python
def test_your_module(self):
    """Test your module"""
    self.section("MODULE: YOUR MODULE")
    
    # Add your test cases
    self.run_test(
        name="Your Test Name",
        module="your_module",
        method="GET",
        endpoint="/your-endpoint",
        headers=self.context.headers,
        expected_status=200,
        critical=True  # Mark as critical for smoke tests
    )
```

### Adding New Modules

1. Create a new test method in `TestRunner` class
2. Add the module to the `test_modules` list in `run()` method
3. Implement test cases using `run_test()` method
4. Update this documentation

## Support

For issues or questions:
1. Check the log file: `e2e_test_results.log`
2. Review the HTML report for detailed error information
3. Run the failing module in isolation
4. Check backend logs for server-side errors

## Version History

- **v1.0** - Initial comprehensive E2E test suite
  - 23+ modules covered
  - Multiple report formats
  - Test data management
  - CI/CD integration ready
