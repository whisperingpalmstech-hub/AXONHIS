# Abhay-Sir Branch Implementation - User Guide

## Overview

This guide provides comprehensive instructions for testing and using the new features implemented in the `abhay-sir` branch of AXONHIS. This branch includes:

1. **QA Module** - Quality Assurance with health checks, database checks, logic checks, performance checks, and PDF report generation
2. **Billing Module Enhancements**
   - Package Management with versioning, inclusions/exclusions, pricing, and approval workflow
   - Multi-stage Billing (interim, intermediate, final bills) with partial payments and refunds
   - Variable Pricing Engine with patient category, bed type, payment entitlement, and after-hours charging
   - Contract Management with inclusions/exclusions, co-pay, CAP amounts, credit limits
   - Deposit Management with security deposits, active deposits, and family deposits with OTP
   - Taxation Module with tax master, applicability, and GST/Tax calculation
   - Credit Patient Billing with authorization, co-pay splitting, denials, invoices, and settlements
3. **Stock Management Enhancements**
   - Stock Movement Analytics with inter-store transfers, approval workflow, and movement reports
   - Expiry Management with alerts, tracking, return to supplier, and discount sales
   - Stock Valuation with FIFO/LIFO/moving average methods and stock adjustments
   - Physical Stock Verification with schedules, items, discrepancies, and reports

## Branch Information

- **Branch Name**: `abhay-sir`
- **Base Branch**: `main`
- **Status**: All features implemented and committed

## QA Module Testing

### Accessing QA Panels

The QA module is integrated into all three frontend applications:

1. **Main Application**: Navigate to `/qa`
2. **Patient Portal**: Navigate to `/qa`
3. **AxonHIS MD**: Navigate to `/qa`

### QA Panel Features

Each QA panel provides:

- **Test Suites**: View available test suites organized by module (billing, stock, database, api)
- **Run Tests**: Manually trigger test suite execution
- **View Results**: See detailed test results with status, execution time, and error messages
- **Generate Reports**: Create PDF reports from test results
- **Download Reports**: Download templated PDF reports

### Test Suite Categories

#### Billing Module Tests
- Package Creation Validation
- Package Rate Calculation
- Stock Movement
- Stock Valuation
- Billing Workflow
- Discount Authorization

#### Stock Module Tests
- Database Connection Health
- Table Access Checks
- Query Performance
- Data Integrity

#### API Health Tests
- Health Endpoint Check
- API Docs Endpoint Check

### Running QA Tests

1. Navigate to the QA panel in any frontend app
2. Select a test suite from the list
3. Click "Run" to execute the test suite
4. View results in the "Test Results" section
5. Click "Generate Report" to create a PDF report
6. Click "Download PDF" to save the report

### API Endpoints

The QA module exposes the following API endpoints:

- `GET /api/v1/qa/suites` - List test suites
- `POST /api/v1/qa/suites/{suite_id}/run` - Run a test suite
- `POST /api/v1/qa/reports/generate` - Generate a QA report
- `GET /api/v1/qa/reports` - List QA reports

## Billing Module Enhancements

### Package Management

#### Creating a Package

```bash
POST /api/v1/billing/packages
{
  "name": "Surgery Package",
  "description": "Complete surgery package",
  "package_type": "ipd",
  "base_price": 50000,
  "inclusions": [
    {
      "service_id": "service-uuid",
      "service_name": "Surgery",
      "service_type": "hospital_service",
      "quantity": 1
    }
  ],
  "exclusions": [],
  "pricing": [
    {
      "patient_category": "national",
      "bed_type": "general",
      "price": 50000
    }
  ]
}
```

#### Package Features

- **Versioning**: Each package update creates a new version
- **Inclusions/Exclusions**: Define which services are included or excluded
- **Multi-tier Pricing**: Different prices for patient category, bed type, payment entitlement
- **Approval Workflow**: Forceful inclusion/exclusion requires approval
- **Profit Tracking**: Track package profit per patient

### Multi-Stage Billing

#### Creating Bill Stages

```bash
POST /api/v1/billing/stages/bills/{bill_id}/interim
POST /api/v1/billing/stages/bills/{bill_id}/intermediate
POST /api/v1/billing/stages/bills/{bill_id}/final
```

#### Bill Stage Features

- **Interim Bills**: Initial bill before completion
- **Intermediate Bills**: Progress bills during treatment
- **Final Bills**: Final settlement bill
- **Partial Payments**: Accept partial payments on bills
- **Bill Holds**: Put bills on hold for various reasons
- **Refunds**: Process refund requests with approval workflow
- **Credit/Debit Notes**: Create post-bill adjustments

### Variable Pricing Engine

#### Calculating Service Price

```bash
POST /api/v1/billing/pricing/calculate
{
  "service_id": "service-uuid",
  "patient_category": "national",
  "bed_type": "private",
  "payment_entitlement": "self"
}
```

#### Pricing Features

- **Base Rates**: Master rates for each service
- **Rate Variations**: Adjustments based on patient category, bed type, payment entitlement
- **Validity Periods**: Time-based rate changes
- **After-Hours Charging**: Additional charges for services outside working hours
- **Multi-Currency Support**: Automatic currency conversion

### Contract Management

#### Creating a Contract

```bash
POST /api/v1/billing/contracts
{
  "contract_number": "CTR-2024-001",
  "contract_name": "ABC Corporation",
  "contract_type": "corporate",
  "company_name": "ABC Corporation",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z"
}
```

#### Contract Features

- **Inclusions/Exclusions**: Define covered and excluded services
- **Co-Pay Configuration**: Set co-pay percentages and limits
- **CAP Amounts**: Define usage limits per visit, month, year, or lifetime
- **Credit Limits**: Set credit limits with reset periods
- **Payment Terms**: Configure payment mode, credit period, discounts, penalties
- **Employee Grades**: Define employee-specific discounts and limits

### Deposit Management

#### Creating a Deposit

```bash
POST /api/v1/billing/deposits/deposits
{
  "patient_id": "patient-uuid",
  "deposit_type": "security",
  "amount": 10000,
  "payment_method": "cash",
  "is_refundable": true
}
```

#### Deposit Features

- **Security Deposits**: Refundable deposits for credit patients
- **Active Deposits**: Non-refundable deposits
- **Family Deposits**: Shared deposits with OTP verification
- **Deposit Usage**: Track deposit usage against bills
- **Refund Processing**: Request and process refunds with approval

### Taxation Module

#### Creating a Tax

```bash
POST /api/v1/billing/tax/taxes
{
  "tax_code": "GST",
  "tax_name": "Goods and Services Tax",
  "tax_type": "gst",
  "tax_percentage": 18,
  "effective_from": "2024-01-01T00:00:00Z"
}
```

#### Tax Features

- **Tax Master**: Define taxes (GST, service tax, VAT, cess, surcharge)
- **Tax Applicability**: Define which services are taxable
- **Validity Periods**: Time-based tax rate changes
- **Automatic Calculation**: Automatic tax calculation on bills

### Credit Patient Billing

#### Creating Authorization

```bash
POST /api/v1/billing/credit/authorizations
{
  "patient_id": "patient-uuid",
  "contract_id": "contract-uuid",
  "authorized_amount": 100000,
  "valid_from": "2024-01-01T00:00:00Z"
}
```

#### Credit Billing Features

- **Authorization Tracking**: Track pre-authorization limits
- **Co-Pay Splitting**: Split bills between patient and company
- **Denial Handling**: Track and manage claim denials
- **Invoice Generation**: Create and send invoices to credit companies
- **Invoice Settlements**: Track invoice payments
- **Security Deposit Adjustment**: Adjust security deposits for credit billing

## Stock Management Enhancements

### Stock Movement Analytics

#### Creating Inter-Store Transfer

```bash
POST /api/v1/inventory/movement/transfers
{
  "from_store_id": "store-uuid-1",
  "to_store_id": "store-uuid-2",
  "indent_id": "indent-uuid"
}
```

#### Movement Features

- **Inter-Store Transfers**: Move stock between stores
- **Approval Workflow**: Multi-level approval for transfers
- **Transfer Tracking**: Track transfer status (pending, approved, in-transit, received)
- **Movement Reports**: Generate movement analytics reports
- **Store Analytics**: Track receipts, issues, consumption by store

### Expiry Management

#### Checking Expiry Status

```bash
GET /api/v1/inventory/expiry/expiry-status
GET /api/v1/inventory/expiry/near-expiry?days_threshold=30
GET /api/v1/inventory/expiry/expired
```

#### Expiry Features

- **Expiry Alerts**: Configure warning thresholds
- **Expiry Tracking**: Track expiring batches
- **Expiry Reports**: Generate expiry reports
- **Return to Supplier**: Process returns for expired items
- **Discount Sales**: Create discount sales for near-expiry items

### Stock Valuation

#### Calculating Stock Value

```bash
POST /api/v1/inventory/valuation/valuations
{
  "store_id": "store-uuid",
  "valuation_method": "fifo"
}
```

#### Valuation Features

- **FIFO/LIFO**: Calculate stock value using FIFO or LIFO method
- **Moving Average**: Calculate using moving average
- **Stock Adjustments**: Record valuation adjustments
- **Valuation Reports**: Generate valuation reports by store and date

### Physical Stock Verification

#### Creating Verification Schedule

```bash
POST /api/v1/inventory/verification/verification-schedules
{
  "store_id": "store-uuid",
  "verification_type": "full",
  "scheduled_date": "2024-01-15T00:00:00Z"
}
```

#### Verification Features

- **Verification Schedules**: Schedule full, partial, or category-based verifications
- **Item Verification**: Verify actual quantities against system quantities
- **Discrepancy Tracking**: Track shortages, excess, and damage
- **Discrepancy Resolution**: Investigate and resolve discrepancies
- **Verification Reports**: Generate comprehensive verification reports

## Testing Checklist

### QA Module
- [ ] Access QA panel in main frontend app
- [ ] Access QA panel in patient-portal
- [ ] Access QA panel in axonhis-md
- [ ] Run billing module test suite
- [ ] Run stock module test suite
- [ ] Generate QA report
- [ ] Download PDF report

### Billing Module
- [ ] Create a package with inclusions and pricing
- [ ] Create package version
- ] Request forceful inclusion approval
- [ ] Create interim bill
- [ ] Create intermediate bill
- ] Create final bill
- [ ] Process partial payment
- ] Put bill on hold
- ] Process refund request
- ] Create variable pricing rule
- ] Calculate service price
- ] Create contract
- ] Add contract inclusions/exclusions
- ] Set co-pay configuration
- ] Set CAP amount
- ] Set credit limit
- ] Create security deposit
- ] Create family deposit
- ] Assign patient to credit company
- ] Create tax
- ] Set tax applicability
- ] Create authorization
- ] Check authorization limit
- ] Create co-pay split
- ] Process denial
- ] Generate invoice
- ] Settle invoice

### Stock Management
- [ ] Create inter-store transfer
- ] Add items to transfer
- ] Approve transfer
- ] Execute transfer
- ] Receive transfer
- ] Generate movement report
- [ ] Get store movement analytics
- [ ] Create expiry alert
- ] Check expiry status
- ] Generate expiry report
- ] Process return to supplier
- ] Create discount sale
- ] Create valuation method
- ] Calculate stock value
- ] Create stock adjustment
- ] Create verification schedule
- ] Add items to verification
- ] Verify item
- ] Complete verification
- ] Resolve discrepancy

## Troubleshooting

### QA Panel Not Loading

1. Ensure the backend is running
2. Check API endpoint `/api/v1/qa/suites` is accessible
3. Check browser console for errors
4. Verify CORS settings

### Test Suite Execution Fails

1. Check if test definition is active
2. Verify test data is configured correctly
3. Check backend logs for errors
4. Ensure database connection is working

### PDF Report Generation Fails

1. Ensure PDF generation library is installed (weasyprint or reportlab)
2. Check file system permissions for `/tmp` directory
3. Verify report data is complete
4. Check backend logs for errors

## Deployment Notes

### Database Migrations

The new modules require database migrations. Run:

```bash
cd backend
alembic upgrade head
```

### Seeding Test Suites

To seed the test suites for QA module:

```bash
cd backend
python seed_qa_test_suites.py
```

### Environment Variables

Ensure the following environment variables are set:

- `DATABASE_URL`: PostgreSQL connection string
- `BACKEND_CORS_ORIGINS`: CORS origins for frontend access

## Support

For issues or questions related to the abhay-sir branch implementation:

1. Check the documentation in `docs/` directory
2. Review the implementation plan in `.windsurf/plans/abhay-sir-implementation-321ffa.md`
3. Check the git commit history for recent changes
4. Review the original gap analysis in `.windsurf/plans/his-gap-analysis-321ffa.md`

## Summary

The abhay-sir branch implements comprehensive enhancements to the AXONHIS system focusing on:

1. **Quality Assurance** with automated testing and reporting
2. **Billing Module** with advanced features for package management, multi-stage billing, variable pricing, contracts, deposits, taxation, and credit patient billing
3. **Stock Management** with movement analytics, expiry management, stock valuation, and physical stock verification
4. **User Interface** with QA panels integrated into all three frontend applications
5. **Documentation** with comprehensive user guide for testing and using new features

All features are implemented, committed, and ready for testing on the abhay-sir branch.
