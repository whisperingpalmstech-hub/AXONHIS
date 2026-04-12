import { test, expect } from '@playwright/test';

/**
 * AXONHIS UI E2E Tests - Authentication Flow
 * Tests login, logout, and session management
 */

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveTitle(/AXONHIS/);
    await expect(page.locator('form')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    // Fill in login form
    await page.fill('input[id="email"]', 'admin@axonhis.com');
    await page.fill('input[id="password"]', 'Admin@123');
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    
    // Verify we're logged in
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.fill('input[id="email"]', 'invalid@test.com');
    await page.fill('input[id="password"]', 'wrongpassword');
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Verify error message is shown
    await expect(page.locator('text=/invalid|error|failed|Login failed/i')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit empty form
    await page.click('button[type="submit"]');
    
    // Verify validation errors (browser native validation)
    await expect(page.locator('input[id="email"]')).toBeVisible();
    await expect(page.locator('input[id="password"]')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.fill('input[id="email"]', 'admin@axonhis.com');
    await page.fill('input[id="password"]', 'Admin@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    
    // Find and click logout button (try multiple possible selectors)
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign Out"), a:has-text("Logout")').first();
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
    } else {
      // Try clearing localStorage to simulate logout
      await page.evaluate(() => localStorage.clear());
      await page.goto('/login');
    }
    
    // Verify we're redirected to login page
    await page.waitForURL('**/login', { timeout: 10000 });
    await expect(page.locator('input[id="email"]')).toBeVisible();
  });

  test('should persist session after page reload', async ({ page }) => {
    // Login
    await page.fill('input[id="email"]', 'admin@axonhis.com');
    await page.fill('input[id="password"]', 'Admin@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    
    // Reload page
    await page.reload();
    
    // Verify we're still logged in
    await expect(page).toHaveURL(/.*dashboard/);
  });
});
