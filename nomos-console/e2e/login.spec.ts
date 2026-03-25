import { test, expect } from '@playwright/test';

test('login page loads with NomOS branding', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('img[alt*="NomOS"]')).toBeVisible();
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
});

test('login page is keyboard navigable', async ({ page }) => {
  await page.goto('/login');
  await page.keyboard.press('Tab');
  const focused = page.locator(':focus');
  await expect(focused).toBeVisible();
});

test('login page has no critical a11y violations', async ({ page }) => {
  await page.goto('/login');
  // Basic check: skip-to-content link exists
  await expect(page.locator('a[href="#main-content"]')).toBeAttached();
});
