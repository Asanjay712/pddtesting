// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * Navigation Test Suite
 * Tests routing, deep links, and navigation between screens.
 */
test.describe('🧭 Navigation & Routing', () => {

  // All defined routes in the Expo Router app
  const appRoutes = [
    { path: '/',               name: 'Root / Index' },
    { path: '/splash',         name: 'Splash Screen' },
    { path: '/onboarding',     name: 'Onboarding' },
    { path: '/login',          name: 'Login' },
    { path: '/signup',         name: 'Sign Up' },
    { path: '/forgot-password',name: 'Forgot Password' },
    { path: '/dashboard',      name: 'Dashboard' },
    { path: '/upload',         name: 'Upload' },
    { path: '/results',        name: 'Results' },
    { path: '/history',        name: 'History' },
    { path: '/alerts',         name: 'Alerts' },
    { path: '/profile',        name: 'Profile' },
    { path: '/review',         name: 'Code Review' },
    { path: '/assistant',      name: 'AI Assistant' },
    { path: '/settings',       name: 'Settings' },
  ];

  // ── Route existence check for all screens ─────────────────────────
  for (const route of appRoutes) {
    test(`TC-NAV-ROUTE: ${route.name} (${route.path}) does not return 404`, async ({ page }) => {
      await page.goto(route.path);
      await page.waitForLoadState('networkidle');

      // Should NOT be a 404 page
      const bodyText = await page.locator('body').innerText().catch(() => '');
      const url      = page.url();

      // Valid: landed on route OR was redirected to login/splash (auth guard)
      expect(url).not.toMatch(/\/404/i);
      // Page must have some content
      expect(bodyText.length).toBeGreaterThan(0);
    });
  }

  test('TC-NAV-001: Root URL redirects or serves app content', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // After navigation, should be on a valid route
    const finalUrl = page.url();
    const validRoutes = [
      /\/splash/, /\/login/, /\/onboarding/, /\/dashboard/, /\/$/
    ];
    const isValid = validRoutes.some((r) => r.test(finalUrl));
    expect(isValid).toBe(true);
  });

  test('TC-NAV-002: Browser back button works between screens', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    await page.goto('/signup');
    await page.waitForLoadState('networkidle');

    // Go back
    await page.goBack();
    await page.waitForLoadState('networkidle');

    const url = page.url();
    expect(url).toMatch(/\/login/i);
  });

  test('TC-NAV-003: Direct URL navigation to login works', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toMatch(/\/login/i);
  });

  test('TC-NAV-004: Direct URL navigation to signup works', async ({ page }) => {
    await page.goto('/signup');
    await page.waitForLoadState('networkidle');
    expect(page.url()).not.toMatch(/404/);
  });

  test('TC-NAV-005: Page refresh preserves route (SPA routing)', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Refresh
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Should still be on login (404.html fallback handles SPA routing)
    const url = page.url();
    expect(url).not.toMatch(/404/);
  });

  test('TC-NAV-006: Invalid route shows fallback (not blank)', async ({ page }) => {
    await page.goto('/this-route-does-not-exist');
    await page.waitForLoadState('networkidle');

    // Should show the app (404.html = index.html) or redirect
    const bodyText = await page.locator('body').innerText().catch(() => '');
    expect(bodyText.length).toBeGreaterThan(0);
  });

  test('TC-NAV-007: All nav screenshots captured', async ({ page }) => {
    const screenshotRoutes = ['/login', '/signup', '/forgot-password', '/dashboard'];
    for (const route of screenshotRoutes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');
      const filename = route.replace('/', '').replace('/', '-') || 'root';
      await page.screenshot({
        path: `test-results/screenshots/nav-${filename}.png`,
        fullPage: true,
      });
    }
  });
});
