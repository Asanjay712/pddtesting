// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright E2E Configuration
 * Medical AI Platform — https://Asanjay712.github.io/pddtesting/
 *
 * BASE_URL must point to the LIVE deployed GitHub Pages site.
 * Never run against localhost in CI.
 */
module.exports = defineConfig({
  // ── Test directory ────────────────────────────────────────────────
  testDir: './tests',

  // ── Report output ─────────────────────────────────────────────────
  outputDir: './test-results',

  // ── Reporters ─────────────────────────────────────────────────────
  reporter: [
    ['html',  { outputFolder: './playwright-report', open: 'never' }],
    ['junit', { outputFile: './test-results/junit.xml' }],
    ['list'],
  ],

  // ── Global test settings ──────────────────────────────────────────
  use: {
    // Base URL — set via environment variable in CI; fallback to live site
    baseURL: process.env.BASE_URL || 'https://Asanjay712.github.io/pddtesting/',

    // Always run in headless mode in CI
    headless: true,

    // Browser viewport — mobile-first (matches React Native web)
    viewport: { width: 390, height: 844 },

    // Capture screenshot on test failure
    screenshot: 'only-on-failure',

    // Capture video on test failure
    video: 'retain-on-failure',

    // Record traces on first retry (great for debugging CI failures)
    trace: 'on-first-retry',

    // How long to wait for actions (click, fill, etc.)
    actionTimeout: 15_000,

    // How long to wait for navigations
    navigationTimeout: 30_000,

    // Ignore HTTPS errors (GitHub Pages uses valid certs but just in case)
    ignoreHTTPSErrors: false,

    // Extra headers
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },
  },

  // ── Retry flaky tests on CI ────────────────────────────────────────
  retries: process.env.CI ? 2 : 0,

  // ── Parallel workers ───────────────────────────────────────────────
  workers: process.env.CI ? 2 : undefined,

  // ── Global timeout per test ───────────────────────────────────────
  timeout: 60_000,

  // ── Expect assertion timeout ──────────────────────────────────────
  expect: {
    timeout: 10_000,
  },

  // ── Browser projects ──────────────────────────────────────────────
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 390, height: 844 },
      },
    },
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
      },
    },
  ],

  // ── Global setup / teardown ───────────────────────────────────────
  // globalSetup: './global-setup.js',
  // globalTeardown: './global-teardown.js',
});
