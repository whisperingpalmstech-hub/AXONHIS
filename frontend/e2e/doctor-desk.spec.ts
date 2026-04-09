import { test, expect } from '@playwright/test';

/**
 * AXONHIS UI E2E Tests - Doctor Desk / EMR Workflow
 * Tests doctor consultation, vitals recording, diagnosis, and prescriptions
 */

test.describe('Doctor Desk / EMR Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/');
    await page.fill('input[type="email"]', 'admin@axonhis.com');
    await page.fill('input[type="password"]', 'Admin@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('should navigate to doctor desk', async ({ page }) => {
    // Click on doctor desk menu
    await page.click('text=Doctor Desk, text=EMR, text=Consultation, a:has-text("Doctor")');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    await expect(page).toHaveURL(/.*doctor-desk/);
  });

  test('should view doctor worklist', async ({ page }) => {
    // Navigate to doctor desk
    await page.click('text=Doctor Desk, text=Worklist');
    await page.waitForURL('**/doctor-desk/**/worklist', { timeout: 10000 });
    
    // Verify worklist is displayed
    await expect(page.locator('table, .worklist, .patient-queue')).toBeVisible();
  });

  test('should start consultation', async ({ page }) => {
    // Navigate to doctor desk worklist
    await page.click('text=Doctor Desk');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    // Click on first patient in worklist
    const firstPatient = page.locator('tr, .patient-card, .worklist-item').first();
    await firstPatient.click();
    
    // Wait for consultation page
    await page.waitForTimeout(1000);
    
    // Click start consultation button
    await page.click('button:has-text("Start"), button:has-text("Begin"), button:has-text("Consult")');
    
    // Wait for consultation to start
    await page.waitForTimeout(1000);
    
    // Verify consultation started
    await expect(page.locator('text=/consultation|in progress/i')).toBeVisible();
  });

  test('should record patient vitals', async ({ page }) => {
    // Navigate to doctor desk and start consultation
    await page.click('text=Doctor Desk');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Start")');
    await page.waitForTimeout(1000);
    
    // Navigate to vitals section
    await page.click('text=Vitals, text=Vital Signs');
    await page.waitForTimeout(500);
    
    // Fill vitals
    await page.fill('input[name="temperature"], input[name="temp"]', '98.6');
    await page.fill('input[name="pulse"], input[name="heartRate"]', '72');
    await page.fill('input[name="bpSystolic"], input[name="systolic"]', '120');
    await page.fill('input[name="bpDiastolic"], input[name="diastolic"]', '80');
    await page.fill('input[name="weight"], input[name="bodyWeight"]', '70');
    await page.fill('input[name="height"], input[name="bodyHeight"]', '170');
    
    // Save vitals
    await page.click('button:has-text("Save"), button:has-text("Record")');
    
    // Wait for save
    await page.waitForTimeout(1000);
    
    // Verify vitals saved
    await expect(page.locator('text=/saved|recorded/i')).toBeVisible();
  });

  test('should add diagnosis', async ({ page }) => {
    // Navigate to doctor desk and start consultation
    await page.click('text=Doctor Desk');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Start")');
    await page.waitForTimeout(1000);
    
    // Navigate to diagnosis section
    await page.click('text=Diagnosis, text=Dx');
    await page.waitForTimeout(500);
    
    // Search for diagnosis
    const diagnosisInput = page.locator('input[placeholder*="diagnosis"], input[name="diagnosisSearch"]').first();
    await diagnosisInput.fill('cough');
    await page.waitForTimeout(500);
    
    // Select diagnosis from dropdown
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    
    // Add diagnosis
    await page.click('button:has-text("Add"), button:has-text("Save")');
    
    // Wait for save
    await page.waitForTimeout(1000);
    
    // Verify diagnosis added
    await expect(page.locator('text=/added|saved/i')).toBeVisible();
  });

  test('should create prescription', async ({ page }) => {
    // Navigate to doctor desk and start consultation
    await page.click('text=Doctor Desk');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Start")');
    await page.waitForTimeout(1000);
    
    // Navigate to prescription section
    await page.click('text=Prescription, text=Rx, text=Medication');
    await page.waitForTimeout(500);
    
    // Search for medicine
    const medicineInput = page.locator('input[placeholder*="medicine"], input[name="medicineSearch"]').first();
    await medicineInput.fill('paracetamol');
    await page.waitForTimeout(500);
    
    // Select medicine from dropdown
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    
    // Fill dosage details
    await page.fill('input[name="dosage"], input[name="dose"]', '500mg');
    await page.fill('input[name="frequency"], select[name="frequency"]', 'Twice daily');
    await page.fill('input[name="duration"]', '5 days');
    
    // Add prescription
    await page.click('button:has-text("Add"), button:has-text("Prescribe")');
    
    // Wait for add
    await page.waitForTimeout(1000);
    
    // Verify prescription added
    await expect(page.locator('text=/added|prescribed/i')).toBeVisible();
  });

  test('should complete consultation', async ({ page }) => {
    // Navigate to doctor desk and start consultation
    await page.click('text=Doctor Desk');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Start")');
    await page.waitForTimeout(1000);
    
    // Complete consultation
    await page.click('button:has-text("Complete"), button:has-text("Finish"), button:has-text("End")');
    
    // Wait for completion
    await page.waitForTimeout(1000);
    
    // Verify consultation completed
    await expect(page.locator('text=/completed|finished/i')).toBeVisible();
  });

  test('should view patient history', async ({ page }) => {
    // Navigate to doctor desk
    await page.click('text=Doctor Desk');
    await page.waitForURL('**/doctor-desk/**', { timeout: 10000 });
    
    // Click on first patient
    const firstPatient = page.locator('tr, .patient-card').first();
    await firstPatient.click();
    await page.waitForTimeout(1000);
    
    // Click on history tab
    await page.click('text=History, text=Medical History, text=Past Records');
    await page.waitForTimeout(500);
    
    // Verify history is displayed
    await expect(page.locator('text=/history|records|visits/i')).toBeVisible();
  });
});
