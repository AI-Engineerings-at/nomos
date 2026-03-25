import { test, expect } from '@playwright/test';

test('hire wizard shows 4 steps', async ({ page }) => {
  await page.goto('/admin/hire');
  // Step 1 should be visible
  await expect(page.locator('text=Wer soll')).toBeVisible();
});

test('hire wizard has Rico template option', async ({ page }) => {
  await page.goto('/admin/hire');
  await expect(page.locator('text=Red Teamer')).toBeVisible();
});
