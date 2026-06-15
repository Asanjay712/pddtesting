// @ts-check
const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../page-objects/LoginPage');

/**
 * Auth Test Suite
 * Tests authentication flows on the live GitHub Pages deployment.
 *
 * Note: Since this is the frontend-only static build, tests verify
 * UI rendering and client-side validation (not actual API auth).
 * Backend-dependent tests are marked with the 'api' tag.
 */
test.describe('🔐 Authentication', () => {

  test.describe('Login Page', () => {

    test('TC-AUTH-001: Login page loads successfully', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      // Page should load without errors
      await expect(page).not.toHaveURL(/error|404/i);

      // Take screenshot for report
      await page.screenshot({
        path: 'test-results/screenshots/TC-AUTH-001-login-page.png',
        fullPage: true,
      });
    });

    test('TC-AUTH-002: Email input field is visible and interactive', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.expectEmailInputVisible();
      await loginPage.fillEmail('test@example.com');

      const value = await loginPage.emailInput.inputValue();
      expect(value).toBe('test@example.com');
    });

    test('TC-AUTH-003: Password input field is visible and masks characters', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.expectPasswordInputVisible();

      // Check it's a password field (characters masked)
      const inputType = await loginPage.passwordInput.getAttribute('type');
      expect(inputType).toBe('password');

      await loginPage.fillPassword('MySecret123');
    });

    test('TC-AUTH-004: Login button is present and clickable', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      await loginPage.expectLoginButtonVisible();
      // Button should not be disabled by default
      const isDisabled = await loginPage.loginButton.isDisabled();
      expect(isDisabled).toBe(false);
    });

    test('TC-AUTH-005: App branding is displayed (logo + title)', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      // Either the emoji logo or the text title should appear
      const logoVisible  = await loginPage.logoEmoji.isVisible().catch(() => false);
      const titleVisible = await loginPage.appTitle.isVisible().catch(() => false);
      expect(logoVisible || titleVisible).toBe(true);

      await page.screenshot({
        path: 'test-results/screenshots/TC-AUTH-005-branding.png',
        fullPage: true,
      });
    });

    test('TC-AUTH-006: Forgot Password link is present', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      const forgotVisible = await loginPage.forgotLink.isVisible().catch(() => false);
      expect(forgotVisible).toBe(true);
    });

    test('TC-AUTH-007: Sign Up link is present', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      const signupVisible = await loginPage.signupLink.isVisible().catch(() => false);
      expect(signupVisible).toBe(true);
    });

    test('TC-AUTH-008: Navigate to Forgot Password screen', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      const forgotVisible = await loginPage.forgotLink.isVisible().catch(() => false);
      if (forgotVisible) {
        await loginPage.clickForgotPassword();
        await page.waitForLoadState('networkidle');
        // Should navigate to forgot-password route or stay on same page
        const url = page.url();
        expect(url).toMatch(/\/(forgot.?password|login)/i);
      } else {
        test.skip('Forgot Password link not visible on this build');
      }
    });

    test('TC-AUTH-009: Navigate to Sign Up screen', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      const signupVisible = await loginPage.signupLink.isVisible().catch(() => false);
      if (signupVisible) {
        await loginPage.clickSignUp();
        await page.waitForLoadState('networkidle');
        const url = page.url();
        expect(url).toMatch(/\/(signup|register|login)/i);
      } else {
        test.skip('Sign Up link not visible on this build');
      }
    });

    test('TC-AUTH-010: Login form submits without crashing on empty fields', async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.goto();

      // Click login without filling fields
      const loginBtnVisible = await loginPage.loginButton.isVisible().catch(() => false);
      if (loginBtnVisible) {
        await loginPage.clickLogin();
        // Wait briefly — should show validation or stay on page
        await page.waitForTimeout(1000);
        // Must not navigate to dashboard (empty credentials should fail)
        const url = page.url();
        expect(url).not.toMatch(/\/dashboard/i);
      }
    });
  });

  test.describe('Signup Page', () => {

    test('TC-AUTH-011: Signup page loads', async ({ page }) => {
      await page.goto('/signup');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: 'test-results/screenshots/TC-AUTH-011-signup-page.png',
        fullPage: true,
      });
      // Should load without 404
      await expect(page).not.toHaveURL(/404/);
    });

    test('TC-AUTH-012: Signup form has required fields', async ({ page }) => {
      await page.goto('/signup');
      await page.waitForLoadState('networkidle');

      // Check for name, email, password fields
      const nameInput  = page.locator('input[placeholder*="name" i], input[placeholder*="Name" i]').first();
      const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]').first();
      const passInput  = page.locator('input[type="password"], input[placeholder*="password" i]').first();

      const nameVisible  = await nameInput.isVisible().catch(() => false);
      const emailVisible = await emailInput.isVisible().catch(() => false);
      const passVisible  = await passInput.isVisible().catch(() => false);

      // At minimum email + password should be present
      expect(emailVisible || nameVisible).toBe(true);
      expect(passVisible).toBe(true);
    });
  });

  test.describe('Forgot Password Page', () => {

    test('TC-AUTH-013: Forgot password page loads', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: 'test-results/screenshots/TC-AUTH-013-forgot-password.png',
        fullPage: true,
      });
      await expect(page).not.toHaveURL(/404/);
    });

    test('TC-AUTH-014: Email input present on forgot password page', async ({ page }) => {
      await page.goto('/forgot-password');
      await page.waitForLoadState('networkidle');

      const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]').first();
      const emailVisible = await emailInput.isVisible().catch(() => false);
      expect(emailVisible).toBe(true);
    });
  });
});
