# AXONHIS Manual UI Testing Guide

## Browser Previews Available

**AXONHIS Frontend:** Click the button to open http://localhost:9501
**AXONHIS MD App:** Click the button to open http://localhost:9503

## Test Scenarios

### 1. AXONHIS Frontend - Authentication Flow

**Test 1.1: Login Page Display**
- Navigate to http://localhost:9501
- Verify login page is displayed
- Check for email and password input fields
- Verify login button is present
- Check for any error messages (should be none initially)

**Test 1.2: Valid Login**
- Enter email: `admin@axonhis.com`
- Enter password: `Admin@123`
- Click login button
- Verify redirect to dashboard
- Check for welcome message or user profile

**Test 1.3: Invalid Login**
- Enter email: `invalid@test.com`
- Enter password: `wrongpassword`
- Click login button
- Verify error message is displayed
- Check that user stays on login page

**Test 1.4: Empty Form Validation**
- Leave email and password fields empty
- Click login button
- Verify validation errors appear
- Check for required field indicators

### 2. AXONHIS Frontend - Dashboard Navigation

**Test 2.1: Dashboard Layout**
- After login, verify dashboard loads
- Check for navigation menu/sidebar
- Verify dashboard widgets/cards are displayed
- Check for user profile/logout options

**Test 2.2: Module Navigation**
- Click on "Patients" module
- Verify patient management page loads
- Check for patient list or search options
- Return to dashboard

- Click on "OPD" module
- Verify OPD management page loads
- Check for OPD queue or visit options
- Return to dashboard

- Click on "Lab" module
- Verify Lab management page loads
- Check for lab orders or results options
- Return to dashboard

**Test 2.3: Responsive Design**
- Resize browser window
- Verify layout adjusts appropriately
- Check navigation menu on mobile view
- Verify content remains accessible

### 3. AXONHIS Frontend - Patient Registration

**Test 3.1: Navigate to Patient Registration**
- From dashboard, navigate to Patients
- Click "New Patient" or "Register Patient"
- Verify patient registration form loads

**Test 3.2: Fill Patient Form**
- Enter first name: `Test`
- Enter last name: `Patient`
- Enter email: `test@axonhis.com`
- Enter phone: `9876543210`
- Select gender: `Male`
- Enter date of birth: `1990-05-15`
- Enter address details
- Click submit/register button

**Test 3.3: Form Validation**
- Try to submit empty form
- Check for required field errors
- Try invalid email format
- Verify validation messages appear

**Test 3.4: Patient Search**
- Navigate to Patients list
- Use search field to find patient
- Verify search results appear
- Click on a patient to view details

### 4. AXONHIS Frontend - OPD Workflow

**Test 4.1: Create OPD Visit**
- Navigate to OPD module
- Click "New Visit" or "Create Visit"
- Select patient from dropdown or search
- Select doctor
- Select department
- Enter chief complaint
- Click submit

**Test 4.2: View OPD Queue**
- Navigate to OPD Queue/Worklist
- Verify patient list is displayed
- Check for patient details in queue
- Verify status indicators

**Test 4.3: Start Consultation**
- From OPD queue, click on a patient
- Click "Start Consultation" button
- Verify consultation interface loads
- Check for vitals, diagnosis, prescription sections

**Test 4.4: Complete Consultation**
- Fill in consultation details
- Add diagnosis if applicable
- Add prescription if needed
- Click "Complete" or "Finish" button
- Verify consultation is marked as complete

### 5. AXONHIS MD App - Authentication

**Test 5.1: MD App Login**
- Navigate to http://localhost:9503
- Verify login page loads
- Enter credentials
- Click login
- Verify redirect to MD dashboard

**Test 5.2: MD Dashboard**
- Verify MD-specific dashboard loads
- Check for MD-specific modules (Patients, Appointments, Encounters)
- Verify layout and navigation

**Test 5.3: MD Patient Management**
- Navigate to Patients in MD app
- Verify patient list or search
- Check for patient details view
- Test patient creation if available

**Test 5.4: MD Appointment Management**
- Navigate to Appointments in MD app
- Verify appointment calendar/list
- Check for appointment creation options
- Test appointment scheduling if available

**Test 5.5: MD Encounter Management**
- Navigate to Encounters in MD app
- Verify encounter list
- Check for encounter details
- Test encounter creation if available

### 6. Cross-Application Integration

**Test 6.1: Data Consistency**
- Create patient in main app
- Verify patient appears in MD app (if integrated)
- Check for data synchronization

**Test 6.2: Session Management**
- Login to main app
- Open MD app in new tab
- Verify session persists or re-authentication required
- Test logout from both applications

## Test Results Template

### Test Execution Log

**Date:** [Fill in date]
**Tester:** [Fill in name]
**Environment:** Development (localhost)

#### Results Summary
- Total Tests: [Number]
- Passed: [Number]
- Failed: [Number]
- Pass Rate: [Percentage]

#### Detailed Results

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| 1.1 | Login Page Display | ✅/❌ | [Notes] |
| 1.2 | Valid Login | ✅/❌ | [Notes] |
| [etc.] | [etc.] | ✅/❌ | [Notes] |

#### Issues Found
1. [Issue description]
2. [Issue description]

#### Recommendations
1. [Recommendation]
2. [Recommendation]

## Automation Notes

For automated UI testing, the following tools were considered:
- **Playwright** - Encountered permission issues during installation
- **Selenium** - Would require similar setup
- **Python requests** - Used for API-level testing (completed)

Current approach uses manual browser testing through browser previews combined with API-level automated tests for comprehensive coverage.
