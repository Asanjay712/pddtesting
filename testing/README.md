# PancreaScan Medical AI Platform — Testing Guide

> **Comprehensive automated testing suite covering 260+ test cases across 6 test types with automatic XLSX reporting and GitHub Actions CI/CD.**

---

## 📊 Test Suite Overview

| Suite | TC Range | Count | Tool | Coverage |
|-------|----------|-------|------|----------|
| 🔌 **API Functional** | TC-001–050 | 50 | pytest + requests | Auth, Upload, Dashboard, Security |
| 🧩 **Unit Tests** | TC-051–080 | 30 | pytest | MIME, Password hash, ICD/CPT, Greetings |
| 📱 **Appium Mobile** | TC-081–110 | 30 | Appium + UiAutomator2 | Launch, Login, Navigate, Upload |
| 🎨 **UI/UX Validation** | TC-111–130 | 20 | pytest + requests | Deployability, Performance, CORS |
| 🌐 **Selenium Web** | TC-S001–S080 | 80 | Selenium + Chrome | Page load, Forms, Navigation, A11y |
| ⚙️ **Functional E2E** | TC-F001–F050 | 50 | pytest + requests | User journeys, Upload flow, Edge cases |
| **📊 TOTAL** | | **260** | | |

**Security Scans** (separate pipeline):
| Tool | Purpose |
|------|---------|
| Gitleaks | Secret / credential scanning across all commits |
| Semgrep | SAST — Python, JavaScript, OWASP Top 10, JWT |
| Trivy | Dependency CVE scan |
| pip-audit | Python package vulnerability audit |
| Custom Analysis | 10 custom checks (CORS, JWT, rate limiting, etc.) |

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
cd testing
pip install -r requirements_test.txt

# 2. Run all tests
pytest api/ unit/ selenium/ functional/ -v --junitxml=reports/master.xml

# 3. Generate XLSX report
python generate_test_report.py

# 4. Generate Issues report (only failures)
python generate_issues_report.py
```

---

## 🚀 Run Individual Suites

```bash
# API & UI/UX tests
pytest testing/api/ -v --junitxml=testing/reports/api_junit.xml

# Unit tests
pytest testing/unit/ -v --junitxml=testing/reports/unit_junit.xml

# Selenium web tests (requires Chrome + live site)
SELENIUM_BASE_URL=https://tilaksai99.github.io/pddtesting \
  pytest testing/selenium/ -v --junitxml=testing/reports/selenium_junit.xml

# Functional E2E tests (requires live API)
API_BASE_URL=http://10.33.115.98:8000 \
  pytest testing/functional/ -v --junitxml=testing/reports/functional_junit.xml

# Appium mobile tests (requires Appium server + device/emulator)
APPIUM_HOST=127.0.0.1 APPIUM_PORT=4723 \
  pytest testing/appium/ -v --junitxml=testing/reports/mobile_junit.xml
```

---

## 📊 Report Generation

### Full E2E XLSX Report
```bash
cd testing
# With real JUnit XML results (dynamic — shows real PASS/FAIL)
python generate_test_report.py

# With specific XML files
python generate_test_report.py --junit reports/api_junit.xml reports/unit_junit.xml

# Static mode (all PASS — offline demo)
python generate_test_report.py --static
```
**Output:** `testing/reports/E2E_Test_Report_PancreaScan_<timestamp>.xlsx`  
**Sheets:** 📊 Summary · 📋 All Test Cases · 🔌 API · 🧩 Unit · 📱 Mobile · 🌐 Web · ⚙️ Functional · 🚀 Run Commands

### Issues Report (Failed Tests Only)
```bash
cd testing
python generate_issues_report.py
```
**Output:** `testing/reports/Issues_Report_PancreaScan_<timestamp>.xlsx`  
*(Only generated when failures exist)*  
**Sheets:** 🚨 Issues Summary · ❌ Failed Tests · 🔁 How to Reproduce · ✅ Fix Checklist

### Security XLSX Report
```bash
python scripts/generate_security_xlsx.py \
  --semgrep   scan-outputs/semgrep-results.json \
  --trivy     scan-outputs/trivy-results.json \
  --pip-audit scan-outputs/pip-audit-results.json \
  --custom    scan-outputs/custom-analysis.json
```
**Output:** `Vulnerability Test Results/Security_Report_<timestamp>.xlsx`  
**Sheets:** 🔒 Summary · 🔍 All Findings · 📋 OWASP Top 10 · 📦 Dependency CVEs

---

## 🤖 GitHub Actions — Automated Pipeline

The **Master Test Pipeline** (`master-test-pipeline.yml`) runs automatically on every push and PR.

### Pipeline Jobs

```
Push / PR → GitHub Actions
     │
     ├─── 🧩 unit-tests     ──────┐
     ├─── 🔌 api-tests      ──────┤
     ├─── 🌐 selenium-tests ──────┤──→ 📊 generate-reports ──→ 📝 pipeline-summary
     ├─── ⚙️ functional-tests────┤        │                          │
     ├─── 📱 appium-tests   ──────┤    Downloads all JUnit XMLs      │
     └─── 🔒 security-scan  ──────┘    Generates XLSX reports         │
                                        Uploads as Artifacts          │
                                                                       ▼
                                                            GitHub Step Summary
```

### Download Reports

1. Go to **GitHub → Actions → Latest Run**
2. Scroll to **Artifacts** at the bottom
3. Download:
   - `📊 master-test-report-xlsx` — Full XLSX (all 260 tests)
   - `⚠️ issues-report-xlsx` — Failures only (if any)
   - `🔒 security-report-xlsx` — Vulnerability findings

---

## 🔁 Fix & Re-Test Workflow

```
1. Tests fail → Issues Report auto-generated
2. Download "issues-report-xlsx" from GitHub Artifacts
3. Open "Fix Checklist" sheet — see exactly what failed
4. Open "How to Reproduce" sheet — run the failing test locally
5. Fix the code
6. git add . && git commit -m "fix: resolve test failures" && git push
7. Master pipeline auto-runs → new clean report generated
```

---

## 🔧 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_BASE_URL` | `http://10.33.115.98:8000` | Backend API server URL |
| `SELENIUM_BASE_URL` | `https://tilaksai99.github.io/pddtesting` | Selenium test target URL |
| `APPIUM_HOST` | `127.0.0.1` | Appium server host |
| `APPIUM_PORT` | `4723` | Appium server port |

Set GitHub repository **Secrets** at:  
`Settings → Secrets and Variables → Actions → New repository secret`

---

## 🗂️ Directory Structure

```
testing/
├── api/
│   ├── test_api_functional.py      # TC-001–050 (API tests)
│   └── test_uiux_validation.py     # TC-111–130 (UI/UX tests)
├── unit/
│   └── test_unit.py               # TC-051–080 (Unit tests)
├── appium/
│   └── test_appium_mobile.py      # TC-081–110 (Mobile tests)
├── selenium/
│   ├── conftest_selenium.py        # Chrome driver fixtures
│   └── test_selenium_web.py       # TC-S001–S080 (Selenium tests)
├── functional/
│   └── test_functionality.py      # TC-F001–F050 (E2E functional)
├── reports/                        # Generated reports output
├── generate_test_report.py         # Master XLSX generator (dynamic)
├── generate_issues_report.py       # Issues-only XLSX generator
├── requirements_test.txt           # Test dependencies
└── README.md                       # This file

scripts/
├── security_analysis.py            # Custom static security analysis
└── generate_security_xlsx.py       # Security XLSX report generator

.github/workflows/
├── master-test-pipeline.yml        # ← NEW: Unified master pipeline
├── app-testing.yml                 # Legacy: existing test pipeline
├── deploy-and-test.yml             # Legacy: Playwright E2E + deploy
└── security-review.yml            # Legacy: security scans
```

---

## 🔒 Security Testing Coverage

| Check | Tool | Status |
|-------|------|--------|
| Secret / credential leaks | Gitleaks | ✅ Active |
| Python security patterns | Semgrep | ✅ Active |
| OWASP Top 10 | Semgrep | ✅ Active |
| JWT vulnerabilities | Semgrep | ✅ Active |
| Dependency CVEs | Trivy | ✅ Active |
| Python package CVEs | pip-audit | ✅ Active |
| Weak password hashing | Custom | ✅ Active |
| Hardcoded secrets | Custom | ✅ Active |
| CORS misconfiguration | Custom | ✅ Active |
| Missing rate limiting | Custom | ✅ Active |
| SQL injection patterns | Custom | ✅ Active |
| JWT without expiry | Custom | ✅ Active |
| Missing auth on endpoints | Custom | ✅ Active |
| Debug middleware in prod | Custom | ✅ Active |
| File upload safety | Custom | ✅ Active |
| Sensitive data in logs | Custom | ✅ Active |
