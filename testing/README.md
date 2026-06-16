# PancreaScan Medical AI Platform — Testing Guide

> **Comprehensive automated testing suite covering 300 test cases across 6 test types with GitHub Actions CI/CD.**

---

## 📊 Test Suite Overview

| Suite | TC Range | Count | Tool | Coverage |
|-------|----------|-------|------|----------|
| 🔌 **API Functional** | TC-001–050 | 50 | pytest + requests | Auth, Upload, Dashboard, Security |
| 🧩 **Unit Tests** | TC-051–080, TC-U081–U090 | 40 | pytest | MIME, Hashing, ICD/CPT, JWT, Regex |
| 📱 **Appium Mobile** | TC-081–110, TC-M111–M120 | 40 | Appium + UiAutomator2 | Launch, Login, Navigate, Upload, Gestures |
| 🎨 **UI/UX Validation** | TC-111–130 | 20 | pytest + requests | Deployability, Performance, CORS |
| 🌐 **Selenium Web** | TC-S001–S090 | 90 | Selenium + Chrome | Page load, Forms, Navigation, A11y, Performance |
| ⚙️ **Functional E2E** | TC-F001–F060 | 60 | pytest + requests | User journeys, Upload flow, Edge cases, CORS |
| **📊 TOTAL** | | **300** | | |

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
cd testing
pip install -r requirements_test.txt

# 2. Run all tests
pytest -v --junitxml=reports/master.xml

# 3. Run specific suites
pytest unit/ -v          # Unit tests (always pass)
pytest selenium/ -v      # Selenium tests (needs Chrome)
pytest functional/ -v    # Functional tests (needs backend)
pytest appium/ -v        # Appium tests (needs device)
pytest api/ -v           # API tests (needs backend)
```

---

## 🚀 Run Individual Suites

```bash
# Unit tests (no external deps — always pass)
cd testing
python -m pytest unit/test_unit.py -v --junitxml=reports/unit_junit.xml

# Selenium web tests (requires Chrome + internet access)
SELENIUM_BASE_URL=https://tilaksai99.github.io/pddtesting \
  python -m pytest selenium/test_selenium_web.py -v --junitxml=reports/selenium_junit.xml

# Functional E2E tests (requires live API backend)
API_BASE_URL=http://10.33.115.98:8000 \
  python -m pytest functional/test_functionality.py -v --junitxml=reports/functional_junit.xml

# Appium mobile tests (requires Appium server + device/emulator)
APPIUM_HOST=127.0.0.1 APPIUM_PORT=4723 \
  python -m pytest appium/test_appium_mobile.py -v --junitxml=reports/mobile_junit.xml

# API & UI/UX tests (requires live API backend)
API_BASE_URL=http://10.33.115.98:8000 \
  python -m pytest api/ -v --junitxml=reports/api_junit.xml
```

---

## 🤖 GitHub Actions — Automated Pipeline

The **Master Test Pipeline** (`master-test-pipeline.yml`) runs automatically on every push and PR.

### Pipeline Jobs

```
Push / PR → GitHub Actions
     │
     ├─── 🧩 unit-tests        (40 tests)  ── always pass ──┐
     ├─── 🔌 api-tests         (70 tests)  ── skip if no backend ──┤
     ├─── 🌐 selenium-tests    (90 tests)  ── headless Chrome ──┤──→ 📝 pipeline-summary
     ├─── ⚙️ functional-tests  (60 tests)  ── skip if no backend ──┤
     └─── 📱 appium-tests      (40 tests)  ── skip if no device ──┘
```

### How Tests Pass in CI

| Job | Strategy |
|-----|----------|
| **Unit** | Pure logic, no external deps — always passes |
| **Selenium** | Headless Chrome against live GitHub Pages URL |
| **API & UI/UX** | Graceful skip when backend server is offline |
| **Functional** | Graceful skip when backend server is offline |
| **Appium** | Graceful skip — no Appium server or device in CI |

### Download Reports

1. Go to **GitHub → Actions → Latest Run**
2. Scroll to **Artifacts** at the bottom
3. Download JUnit XML + HTML reports per suite:
   - `unit-test-results`
   - `api-test-results`
   - `selenium-test-results`
   - `functional-test-results`
   - `mobile-test-results`

---

## 🔧 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_BASE_URL` | `http://10.33.115.98:8000` | Backend API server URL |
| `SELENIUM_BASE_URL` | `https://tilaksai99.github.io/pddtesting` | Selenium test target URL |
| `APPIUM_HOST` | `127.0.0.1` | Appium server host |
| `APPIUM_PORT` | `4723` | Appium server port |

---

## 🗂️ Directory Structure

```
testing/
├── api/
│   ├── test_api_functional.py      # TC-001–050 (API tests)
│   └── test_uiux_validation.py     # TC-111–130 (UI/UX tests)
├── unit/
│   └── test_unit.py               # TC-051–080, TC-U081–U090 (40 unit tests)
├── appium/
│   └── test_appium_mobile.py      # TC-081–110, TC-M111–M120 (40 mobile tests)
├── selenium/
│   ├── conftest_selenium.py        # Chrome driver fixtures
│   └── test_selenium_web.py       # TC-S001–S090 (90 Selenium tests)
├── functional/
│   └── test_functionality.py      # TC-F001–F060 (60 E2E functional tests)
├── reports/                        # Generated reports output
├── conftest.py                     # Shared fixtures, auth, test config
├── requirements_test.txt           # Test dependencies
├── pytest.ini                      # Pytest configuration
└── README.md                       # This file

.github/workflows/
└── master-test-pipeline.yml        # Single clean CI pipeline
```

---

## 📋 Test Case Index

### Unit Tests (40)
| Range | Category |
|-------|----------|
| TC-051–060 | MIME type inference |
| TC-061–065 | Password hashing |
| TC-066–070 | File size formatting |
| TC-071–075 | ICD-10 / CPT code validation |
| TC-076–080 | Greeting & date logic |
| TC-U081–U090 | JWT structure, email regex, password strength, HTML sanitization |

### Selenium Web Tests (90)
| Range | Category |
|-------|----------|
| TC-S001–S010 | Page load & basic presence |
| TC-S011–S020 | Login screen UI |
| TC-S021–S030 | Registration screen UI |
| TC-S031–S040 | Navigation & routing |
| TC-S041–S050 | Dashboard & stats UI |
| TC-S051–S060 | Upload screen UI |
| TC-S061–S070 | Accessibility & semantics |
| TC-S071–S080 | Performance & error handling |
| TC-S081–S090 | CSS, JS, mixed content, favicon, security, resilience |

### Functional E2E Tests (60)
| Range | Category |
|-------|----------|
| TC-F001–F010 | Registration → Login → Profile journey |
| TC-F011–F020 | Report upload → processing → results |
| TC-F021–F030 | Dashboard stats consistency |
| TC-F031–F040 | Review workflow & role-based access |
| TC-F041–F050 | AI assistant, concurrency, edge cases |
| TC-F051–F060 | Auth errors, CORS, rate limiting, health check |

### Appium Mobile Tests (40)
| Range | Category |
|-------|----------|
| TC-081–090 | App launch & login |
| TC-091–100 | Signup & navigation |
| TC-101–110 | Upload flow & results |
| TC-M111–M120 | Orientation, gestures, background cycle, memory |

### API & UI/UX Tests (70)
| Range | Category |
|-------|----------|
| TC-001–050 | API functional tests |
| TC-111–130 | UI/UX validation |
