import { test, expect } from '@playwright/test';

/**
 * AXONHIS UI E2E Tests - Patient Registration Flow
 * Tests patient registration, search, and management
 */

test.describe('Patient Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.fill('input[type="email"]', 'admin@axonhis.com');
    await page.fill('input[type="password"]', 'Admin@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('should navigate to patient registration', async ({ page }) => {
    // Click on patient registration menu
    await page.click('text=Patients, text=Registration, a:has-text("Patient")');
    await page.waitForURL('**/patients/**', { timeout: 10000 });
    
    await expect(page).toHaveURL(/.*patients/);
  });

  test('should register new patient', async ({ page }) => {
    // Navigate to patient registration
    await page.click('text=Patients, text=New Patient, a:has-text("Register")');
    await page.waitForURL('**/patients/**/register', { timeout: 10000 });
    
    // Fill patient details
    await page.fill('input[name="firstName"], input[id="firstName"]', 'Test');
    await page.fill('input[name="lastName"], input[id="lastName"]', `Patient-${Date.now()}`);
    await page.fill('input[type="email"], input[name="email"]', `test${Date.now()}@axonhis.com`);
    await page.fill('input[type="tel"], input[name="phone"]', '9876543210');
    await page.fill('input[type="date"], input[name="dob"]', '1990-05-15');
    
    // Select gender
    await page.click('select[name="gender"], select[id="gender"]');
    await page.selectOption('select[name="gender"], select[id="gender"]', 'male');
    
    // Fill address
    await page.fill('input[name="address"], textarea[name="address"]', '123 Test Street');
    await page.fill('input[name="city"], input[id="city"]', 'Mumbai');
    await page.fill('input[name="state"], input[id="state"]', 'Maharashtra');
    await page.fill('input[name="pincode"], input[id="pincode"]', '400001');
    
    // Submit form
    await page.click('button[type="submit"], button:has-text("Register"), button:has-text("Save")');
    
    // Wait for success message or redirect
    await page.waitForTimeout(2000);
    
    // Verify patient was created
    await expect(page.locator('text=/success|created|registered/i')).toBeVisible();
  });

  test('should validate required patient fields', async ({ page }) => {
    // Navigate to patient registration
    await page.click('text=Patients, text=New Patient');
    await page.waitForURL('**/patients/**', { timeout: 10000 });
    
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Verify validation errors
    await expect(page.locator('text=/required|mandatory/i')).toBeVisible();
  });

  test('should search for existing patient', async ({ page }) => {
    // Navigate to patients list
    await page.click('text=Patients');
    await page.waitForURL('**/patients', { timeout: 10000 });
    
    // Use search functionality
    const searchInput = page.locator('input[placeholder*="search"], input[placeholder*="Search"], input[name="search"]').first();
    await searchInput.fill('test');
    
    // Wait for search results
    await page.waitForTimeout(1000);
    
    // Verify search results are displayed
    await expect(page.locator('table, .patient-list, .results')).toBeVisible();
  });

  test('should view patient details', async ({ page }) => {
    // Navigate to patients list
    await page.click('text=Patients');
    await page.waitForURL('**/patients', { timeout: 10000 });
    
    // Click on first patient in list
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    
    // Wait for patient details page
    await page.waitForTimeout(1000);
    
    // Verify patient details are displayed
    await expect(page.locator('text=/patient|details|profile/i')).toBeVisible();
  });

  test('should update patient information', async ({ page }) => {
    // Navigate to patients list
    await page.click('text=Patients');
    await page.waitForURL('**/patients', { timeout: 10000 });
    
    // Click on first patient
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    
    // Wait for patient details
    await page.waitForTimeout(1000);
    
    // Click edit button
    await page.click('button:has-text("Edit"), button:has-text("Update")');
    
    // Modify a field
    await page.fill('input[name="phone"], input[name="mobile"]', '9876543211');
    
    // Save changes
    await page.click('button[type="submit"], button:has-text("Save"), button:has-text("Update")');
    
    // Wait for success message
    await page.waitForTimeout(1000);
    await expect(page.locator('text=/success|updated/i')).toBeVisible();
  });
});
