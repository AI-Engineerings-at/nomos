import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  // We mock the login API response
  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Login successful',
        user: { id: 'u-1', email: 'admin@nomos.local', name: 'Joe Admin', role: 'admin' },
        requires_2fa: false,
      }),
      headers: {
        'Set-Cookie': 'nomos_token=mock-token; Path=/; HttpOnly; SameSite=Lax',
      },
    });
  });

  // Mock the /me endpoint
  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ id: 'u-1', email: 'admin@nomos.local', name: 'Joe Admin', role: 'admin' }),
    });
  });

  await page.goto('/login');
  await page.getByLabel(/email|E-Mail/i).fill('admin@nomos.local');
  await page.getByLabel(/password|Passwort/i).fill('nomos');
  await page.getByRole('button', { name: /login/i }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/.*admin/);
  
  // Save storage state
  await page.context().storageState({ path: authFile });
});
