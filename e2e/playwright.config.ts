import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,  // tests share mocked API state — keep sequential
  retries: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    // Block service workers so Playwright route mocks work correctly
    serviceWorkers: 'block',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Lance le dev server Vite automatiquement avant les tests
  webServer: {
    command: 'npm run dev',
    cwd: '../frontend',
    port: 5173,
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
