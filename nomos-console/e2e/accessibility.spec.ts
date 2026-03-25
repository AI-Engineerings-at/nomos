import { test, expect } from '@playwright/test';

test('all pages have lang attribute', async ({ page }) => {
  for (const url of ['/login', '/admin', '/app']) {
    await page.goto(url);
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBeTruthy();
    expect(['de', 'en']).toContain(lang);
  }
});

test('no images without alt text on admin page', async ({ page }) => {
  await page.goto('/admin');
  const imagesWithoutAlt = await page.locator('img:not([alt])').count();
  expect(imagesWithoutAlt).toBe(0);
});
