import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:3040',
  },
  webServer: {
    command: 'npm run dev',
    port: 3040,
    reuseExistingServer: true,
  },
});
