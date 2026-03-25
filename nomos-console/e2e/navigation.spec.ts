import { test, expect } from '@playwright/test';

test('admin layout has sidebar navigation', async ({ page }) => {
  await page.goto('/admin');
  await expect(page.locator('nav')).toBeVisible();
});

test('sidebar shows Mitarbeiter-Metapher labels', async ({ page }) => {
  await page.goto('/admin');
  const nav = page.locator('nav');
  // Should use "Mein Team" not "Fleet"
  // Should use "Einstellen" not "Deploy"
  const text = await nav.textContent();
  expect(text).not.toContain('Fleet');
  expect(text).not.toContain('Deploy');
  expect(text).not.toContain('Agent');
});

test('theme toggle works', async ({ page }) => {
  await page.goto('/admin');
  const html = page.locator('html');
  // Default is light
  const initialTheme = await html.getAttribute('data-theme');
  // Find and click theme toggle
  const toggle = page.locator('button[aria-label*="heme"], button[aria-label*="odus"]');
  if (await toggle.count() > 0) {
    await toggle.first().click();
    const newTheme = await html.getAttribute('data-theme');
    expect(newTheme).not.toBe(initialTheme);
  }
});
