// @ts-check
const { expect } = require('@playwright/test');

/**
 * LoginPage — Page Object Model
 * Encapsulates all interactions with the Login screen.
 *
 * Selectors target text-based identifiers since Expo web renders
 * standard HTML elements from React Native primitives.
 */
class LoginPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;

    // ── Locators ────────────────────────────────────────────────────
    this.emailInput    = page.locator('input[type="email"], input[placeholder*="Email" i], input[placeholder*="email" i]').first();
    this.passwordInput = page.locator('input[type="password"], input[placeholder*="Password" i], input[placeholder*="password" i]').first();
    this.loginButton   = page.locator('button, [role="button"]').filter({ hasText: /^login$/i }).first();
    this.forgotLink    = page.locator('text=/forgot password/i');
    this.signupLink    = page.locator('text=/sign up|create account/i').first();
    this.errorMessage  = page.locator('[role="alert"], text=/invalid|incorrect|error|failed/i').first();
    this.appTitle      = page.locator('text=/Medical AI Platform|Medical Coding/i').first();
    this.logoEmoji     = page.locator('text=🏥').first();
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to the login page.
   * The app starts at root which redirects to splash → login.
   */
  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  async gotoRoot() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  // ── Actions ───────────────────────────────────────────────────────

  async fillEmail(email) {
    await this.emailInput.waitFor({ state: 'visible', timeout: 10_000 });
    await this.emailInput.clear();
    await this.emailInput.fill(email);
  }

  async fillPassword(password) {
    await this.passwordInput.waitFor({ state: 'visible', timeout: 10_000 });
    await this.passwordInput.clear();
    await this.passwordInput.fill(password);
  }

  async clickLogin() {
    await this.loginButton.waitFor({ state: 'visible', timeout: 10_000 });
    await this.loginButton.click();
  }

  async clickForgotPassword() {
    await this.forgotLink.click();
  }

  async clickSignUp() {
    await this.signupLink.click();
  }

  /**
   * Complete login flow: fill email + password, click login.
   */
  async login(email, password) {
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.clickLogin();
  }

  // ── Assertions ────────────────────────────────────────────────────

  async expectLoginPageLoaded() {
    // At minimum the page should load without blank screen
    await expect(this.page).not.toHaveTitle('');
    // Check either the app title or any form input is visible
    const emailVisible = await this.emailInput.isVisible().catch(() => false);
    const titleVisible = await this.appTitle.isVisible().catch(() => false);
    const logoVisible  = await this.logoEmoji.isVisible().catch(() => false);
    expect(emailVisible || titleVisible || logoVisible).toBe(true);
  }

  async expectEmailInputVisible() {
    await expect(this.emailInput).toBeVisible();
  }

  async expectPasswordInputVisible() {
    await expect(this.passwordInput).toBeVisible();
  }

  async expectLoginButtonVisible() {
    await expect(this.loginButton).toBeVisible();
  }

  async expectErrorMessage() {
    await expect(this.errorMessage).toBeVisible({ timeout: 5_000 });
  }

  async expectRedirectedToDashboard() {
    await this.page.waitForURL(/\/(dashboard|home)/i, { timeout: 15_000 });
  }
}

module.exports = { LoginPage };
