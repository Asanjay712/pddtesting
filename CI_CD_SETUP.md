# CI/CD Setup Guide

## Medical AI Platform — GitHub Actions CI/CD Pipeline

This document explains how to configure and use the complete CI/CD pipeline.

---

## 📁 Folder Structure

```
.github/
└── workflows/
    ├── security-review.yml      ← runs on every push/PR
    └── deploy-and-test.yml      ← builds, deploys & tests on every push/PR

e2e/
├── playwright.config.js         ← test configuration (base URL etc.)
├── package.json                 ← Playwright dependencies
├── page-objects/
│   ├── LoginPage.js             ← Login screen interactions
│   ├── DashboardPage.js         ← Dashboard screen interactions
│   └── UploadPage.js            ← Upload screen interactions
└── tests/
    ├── auth.spec.js             ← 14 auth tests (login, signup, forgot-pw)
    ├── dashboard.spec.js        ← 13 dashboard/screen tests
    ├── upload.spec.js           ← 7 upload tests
    ├── navigation.spec.js       ← 22 routing/navigation tests
    └── accessibility.spec.js    ← 10 accessibility tests

scripts/
├── security_analysis.py         ← custom static security checks
├── generate_security_report.py  ← merges all security findings → .md
├── generate_excel_report.py     ← JUnit → .xlsx report
├── generate_html_report.py      ← JUnit → .html report
└── generate_summary.py          ← JUnit → summary.md

Test Results/                    ← created at CI runtime (gitignored)
├── Excel/Automation_Test_Report.xlsx
├── HTML/execution-report.html
├── Screenshots/
├── Logs/
└── Summary/summary.md

Vulnerability Test Results/      ← created at CI runtime (gitignored)
└── security-review.md
```

---

## ⚙️ Step 1 — Enable GitHub Pages

1. Go to: **https://github.com/Asanjay712/pddtesting/settings/pages**
2. Under **"Source"**, select: `GitHub Actions`
3. Click **Save**

> ⚠️ This is REQUIRED for the `deploy-and-test.yml` workflow to work.

---

## 🔑 Step 2 — Add Repository Secrets

Go to: **https://github.com/Asanjay712/pddtesting/settings/secrets/actions**

Click **"New repository secret"** and add:

| Secret Name       | Value                        | Required |
|---|---|---|
| `JWT_SECRET`      | Any random 32+ char string  | Optional (for future backend tests) |
| `DATABASE_URL`    | PostgreSQL connection URL   | Optional (for future backend tests) |

> The security and E2E workflows work **without any secrets** out of the box.
> Secrets are only needed when you add backend API tests later.

---

## 🚀 Step 3 — Trigger the Pipeline

The workflows run automatically on every push. To trigger manually:

1. Go to: **https://github.com/Asanjay712/pddtesting/actions**
2. Click **"Deploy & E2E Test"** workflow
3. Click **"Run workflow"** → **"Run workflow"**

---

## 🌐 Live URLs After Deployment

| Resource | URL |
|---|---|
| **Live App** | https://Asanjay712.github.io/pddtesting/ |
| **E2E Report** | https://Asanjay712.github.io/pddtesting/reports/latest/execution-report.html |
| **Playwright Report** | https://Asanjay712.github.io/pddtesting/reports/latest/playwright/ |

---

## 📊 Viewing Reports

### GitHub Actions Artifacts (always available)
1. Go to **Actions** tab → click any workflow run
2. Scroll to **"Artifacts"** section at the bottom
3. Download:
   - `e2e-test-results` — Excel, HTML, screenshots, logs, JUnit XML
   - `playwright-html-report` — Interactive Playwright report
   - `security-report` — Full security review markdown

### GitHub Actions Step Summary
Each workflow run shows an inline summary in the Actions UI with:
- Pass/fail counts table
- Failed test names and error messages
- Links to the live report URLs

---

## 💻 Local Execution

### Run E2E Tests Locally

```bash
# Install dependencies
cd e2e
npm install
npx playwright install chromium

# Run against live site
BASE_URL=https://Asanjay712.github.io/pddtesting/ npx playwright test

# Run in headed mode (see the browser)
BASE_URL=https://Asanjay712.github.io/pddtesting/ npx playwright test --headed

# Run a specific test file
BASE_URL=https://Asanjay712.github.io/pddtesting/ npx playwright test tests/auth.spec.js

# View interactive HTML report
npx playwright show-report
```

### Run Security Analysis Locally

```bash
# Install Python dependencies
pip install jinja2 openpyxl

# Run custom security analysis
python scripts/security_analysis.py --backend-dir backend --output custom-analysis.json

# Generate full security report
python scripts/generate_security_report.py \
    --custom custom-analysis.json \
    --output "Vulnerability Test Results/security-review.md"

# View the report
cat "Vulnerability Test Results/security-review.md"
```

### Generate Reports from Existing JUnit XML

```bash
pip install openpyxl jinja2 lxml

# Excel
python scripts/generate_excel_report.py \
    --junit e2e/test-results/junit.xml \
    --output "Test Results/Excel/Automation_Test_Report.xlsx"

# HTML
python scripts/generate_html_report.py \
    --junit e2e/test-results/junit.xml \
    --output "Test Results/HTML/execution-report.html"

# Markdown summary
python scripts/generate_summary.py \
    --junit e2e/test-results/junit.xml \
    --output "Test Results/Summary/summary.md"
```

---

## 🔒 Security Workflow Details

**`security-review.yml`** runs these tools in parallel:

| Tool | Purpose | Output |
|---|---|---|
| **Gitleaks** | Secret scanning (API keys, tokens) | SARIF |
| **Semgrep** | SAST: Python + JS + OWASP Top 10 | JSON |
| **Trivy** | Dependency CVE scanning | JSON |
| **pip-audit** | Python package vulnerabilities | JSON |
| **Custom** | Auth checks, hashing, CORS, rate limiting | JSON |

All findings are merged into `Vulnerability Test Results/security-review.md`.

---

## 🧪 E2E Workflow Details

**`deploy-and-test.yml`** runs 4 jobs in sequence:

```
1. build          → npx expo export --platform web
        ↓
2. deploy-app     → GitHub Pages (app only)
        ↓
3. e2e-tests      → Playwright against live URL
                    → Excel + HTML + summary reports
        ↓
4. deploy-reports → GitHub Pages (app + reports combined)
```

**Test suites:** 66 total test cases across 5 files covering:
- Authentication (login, signup, forgot password)
- All 15 app routes
- Navigation and SPA routing
- File upload interface
- Accessibility standards

---

## 🛠️ Troubleshooting

### Workflow not appearing in Actions tab
- Ensure files are in `.github/workflows/` (not just `github/workflows/`)
- YAML syntax must be valid — use https://yaml-online-parser.appspot.com/

### GitHub Pages not serving the app
- Confirm Pages source is set to "GitHub Actions" in repo settings
- Check the `build` job logs for Expo export errors

### Playwright tests failing with "net::ERR_NAME_NOT_RESOLVED"
- The site URL might not be ready yet — the workflow waits up to 6 minutes
- Check the `deploy-app` job to confirm it succeeded first

### Excel report not generating
- Ensure `openpyxl` is installed: `pip install openpyxl`
- Ensure JUnit XML was produced by Playwright (check `e2e/test-results/junit.xml`)

---

## 📦 Dependencies Summary

### E2E (Node.js)
```json
{
  "@playwright/test": "^1.48.0"
}
```

### Report Scripts (Python)
```
openpyxl>=3.1.0
jinja2>=3.1.0
lxml>=5.0.0
```

### CI Tools (installed in Actions)
- `semgrep` (Docker image)
- `gitleaks` (GitHub Action)
- `trivy` (GitHub Action)
- `pip-audit` (pip install)
