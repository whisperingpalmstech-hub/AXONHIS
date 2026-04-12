import { test, expect } from '@playwright/test';

/**
 * AXONHIS UI E2E Tests - OPD Workflow
 * Tests OPD visit creation, queue management, and consultation flow
 */

test.describe('OPD Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.fill('input[type="email"]', 'admin@axonhis.com');
    await page.fill('input[type="password"]', 'Admin@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('should navigate to OPD module', async ({ page }) => {
    // Click on OPD menu
    await page.click('text=OPD, text=Outpatient, a:has-text("OPD")');
    await page.waitForURL('**/opd/**', { timeout: 10000 });
    
    await expect(page).toHaveURL(/.*opd/);
  });

  test('should create new OPD visit', async ({ page }) => {
    // Navigate to OPD visits
    await page.click('text=OPD, text=New Visit');
    await page.waitForURL('**/opd/**/new', { timeout: 10000 });
    
    // Select patient (if patient selection is available)
    const patientSelect = page.locator('select[name="patient"], input[name="patientSearch"]').first();
    if (await patientSelect.isVisible()) {
      await patientSelect.click();
      await page.waitForTimeout(500);
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
    }
    
    // Select doctor
    await page.click('select[name="doctor"], input[name="doctorSearch"]');
    await page.waitForTimeout(500);
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    
    // Select department
    await page.click('select[name="department"]');
    await page.selectOption('select[name="department"]', 'general-medicine');
    
    // Enter chief complaint
    await page.fill('textarea[name="complaint"], input[name="chiefComplaint"]', 'Persistent cough and fever');
    
    // Select visit type
    await page.click('select[name="visitType"]');
    await page.selectOption('select[name="visitType"]', 'new');
    
    // Submit form
    await page.click('button[type="submit"], button:has-text("Create Visit"), button:has-text("Register")');
    
    // Wait for success message
    await page.waitForTimeout(2000);
    await expect(page.locator('text=/success|created|registered/i')).toBeVisible();
  });

  test('should view OPD queue', async ({ page }) => {
    // Navigate to OPD queue
    await page.click('text=OPD, text=Queue, text=Worklist');
    await page.waitForURL('**/opd/**/queue', { timeout: 10000 });
    
    // Verify queue is displayed
    await expect(page.locator('table, .queue-list, .worklist')).toBeVisible();
  });

  test('should filter OPD visits by department', async ({ page }) => {
    // Navigate to OPD visits
    await page.click('text=OPD');
    await page.waitForURL('**/opd/**', { timeout: 10000 });
    
    // Use department filter
    const departmentFilter = page.locator('select[name="department"], .filter-department').first();
    await departmentFilter.click();
    await departmentFilter.selectOption('general-medicine');
    
    // Wait for filtered results
    await page.waitForTimeout(1000);
    
    // Verify filter is applied
    await expect(page.locator('table, .visit-list')).toBeVisible();
  });

  test('should search OPD visits', async ({ page }) => {
    // Navigate to OPD visits
    await page.click('text=OPD');
    await page.waitForURL('**/opd/**', { timeout: 10000 });
    
    // Use search functionality
    const searchInput = page.locator('input[placeholder*="search"], input[name="search"]').first();
    await searchInput.fill('test');
    
    // Wait for search results
    await page.waitForTimeout(1000);
    
    // Verify search results
    await expect(page.locator('table, .visit-list, .results')).toBeVisible();
  });

  test('should view OPD visit details', async ({ page }) => {
    // Navigate to OPD visits
    await page.click('text=OPD');
    await page.waitForURL('**/opd/**', { timeout: 10000 });
    
    // Click on first visit
    const firstVisit = page.locator('tr, .visit-card').first();
    await firstVisit.click();
    
    // Wait for visit details
    await page.waitForTimeout(1000);
    
    // Verify visit details are displayed
    await expect(page.locator('text=/visit|details|patient/i')).toBeVisible();
  });

  test('should update OPD visit status', async ({ page }) => {
    // Navigate to OPD visits
    await page.click('text=OPD');
    await page.waitForURL('**/opd/**', { timeout: 10000 });
    
    // Click on first visit
    const firstVisit = page.locator('tr, .visit-card').first();
    await firstVisit.click();
    
    // Wait for visit details
    await page.waitForTimeout(1000);
    
    // Change visit status
    await page.click('button:has-text("Start"), button:has-text("In Progress")');
    
    // Wait for status update
    await page.waitForTimeout(1000);
    
    // Verify status changed
    await expect(page.locator('text=/in progress|started/i')).toBeVisible();
  });
});
