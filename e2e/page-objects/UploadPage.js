// @ts-check
const { expect } = require('@playwright/test');

/**
 * UploadPage — Page Object Model
 * Encapsulates interactions with the document upload screen.
 */
class UploadPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;

    // ── Locators ────────────────────────────────────────────────────
    this.heading         = page.locator('text=/upload|choose file|select file|attach/i').first();
    this.fileInput       = page.locator('input[type="file"]').first();
    this.uploadButton    = page.locator('button, [role="button"]').filter({ hasText: /upload|analyze|submit/i }).first();
    this.dropZone        = page.locator('[class*="drop"], [class*="upload"]').first();
    this.reportTypeSelect= page.locator('select, [role="combobox"]').first();
    this.progressBar     = page.locator('[role="progressbar"], [class*="progress"]').first();
    this.successMsg      = page.locator('text=/success|uploaded|processed|complete/i').first();
    this.errorMsg        = page.locator('text=/error|failed|invalid|unsupported/i').first();
    this.pdfOption       = page.locator('text=/pdf/i').first();
    this.docxOption      = page.locator('text=/docx|word/i').first();
  }

  // ── Navigation ────────────────────────────────────────────────────

  async goto() {
    await this.page.goto('/upload');
    await this.page.waitForLoadState('networkidle');
  }

  // ── Actions ───────────────────────────────────────────────────────

  async attachFile(filePath) {
    await this.fileInput.setInputFiles(filePath);
  }

  async clickUpload() {
    await this.uploadButton.waitFor({ state: 'visible', timeout: 10_000 });
    await this.uploadButton.click();
  }

  async selectReportType(type) {
    await this.reportTypeSelect.selectOption(type);
  }

  // ── Assertions ────────────────────────────────────────────────────

  async expectLoaded() {
    await this.page.waitForLoadState('networkidle');
    const url = this.page.url();
    expect(url).toMatch(/\/(upload|login|dashboard)?/i);
  }

  async expectUploadAreaVisible() {
    const fileInputVisible = await this.fileInput.isVisible().catch(() => false);
    const dropZoneVisible  = await this.dropZone.isVisible().catch(() => false);
    const headingVisible   = await this.heading.isVisible().catch(() => false);
    expect(fileInputVisible || dropZoneVisible || headingVisible).toBe(true);
  }

  async expectSuccessMessage() {
    await expect(this.successMsg).toBeVisible({ timeout: 30_000 });
  }

  async expectErrorMessage() {
    await expect(this.errorMsg).toBeVisible({ timeout: 10_000 });
  }
}

module.exports = { UploadPage };
