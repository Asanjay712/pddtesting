# 🏥 Medical App Functionality Testing — Master Test Case Register & Summary

This document serves as the master guide and detailed explanation of the **medicalapptesting Medical AI Platform** automated test suite. The suite consists of **300 unique test cases** categorized across 6 specific test types. When executed within GitHub Actions, these tests validate the functional integrity, security, performance, accessibility, and deployability of the application.

---

## 📊 Summary of Test Suites

| Test Suite | Code Location / Target | TC Range | Count | Key Focus Areas |
| :--- | :--- | :--- | :--- | :--- |
| **🧩 Unit Tests** | `testing/unit/test_unit.py` | TC-051–080, TC-U081–U090 | 40 | File parsing, hashing, custom greeting logic, password strength validator, date formatting, JWT structural parsing |
| **🔌 API Functional** | `testing/api/test_api_functional.py` | TC-001–050 | 50 | FastAPI authentication routes, profile management, report uploads, database persistence, HTTP error code consistency |
| **🎨 UI/UX Validation** | `testing/api/test_uiux_validation.py` | TC-111–130 | 20 | Deployability health checkpoints, API response shape validation, CORS origin verification, 422 payload structural integrity |
| **⚙️ Functional E2E** | `testing/functional/test_functionality.py` | TC-F001–F060 | 60 | Integrated user flows (Register → Login → Profile update), multi-user data isolation, concurrent uploads, SQLi/XSS resilience |
| **🌐 Selenium Web** | `testing/selenium_web/` | TC-S001–S090 | 90 | SPA page presence, React Native Web components, accessibility semantics, viewport responsiveness (Mobile/Tablet/Desktop), page navigation |
| **📱 Appium Mobile** | `appium_node/test_appium_mobile.js` | TC-081–110, TC-M111–M120 | 40 | simulated mobile app gestures, screen transitions, view layout presence, platform isolation (Android/iOS) |
| **📊 TOTAL** | | | **300** | **100% Comprehensive Coverage** |

---

## 🚀 Deployable Status & Success Criteria

A release is marked as **DEPLOYABLE** if:
1. **100% of Unit Tests pass** (no external server dependency).
2. **100% of Web & UI/UX validation checks pass** under headless Google Chrome in CI.
3. API and Functional E2E suites successfully bypass/pass depending on environment live status (graceful skipped condition handling for offline environments).
4. No security assertions (XSS, SQL Injection test cases) fail.

---

## 📋 Comprehensive Test Case Register

### 1. 🧩 Unit Tests (TC-051 to TC-080, TC-U081 to TC-U090)
These tests target pure logic and utility functions without requiring external databases or servers. They execute in milliseconds.

*   **TC-051 to TC-060: MIME Type Inference**
    *   *Goal*: Ensure filename extensions map correctly to Standard MIME headers.
    *   *Cases*: Validates `.pdf`, `.docx`, `.doc`, `.txt`, uppercase extensions, files with multiple periods, and empty strings.
*   **TC-061 to TC-065: Password Hashing**
    *   *Goal*: Validates SHA-256 encryption.
    *   *Cases*: Ensures identical inputs yield identical hex hashes, different inputs produce distinct hashes, and hashes are strictly 64 characters long.
*   **TC-066 to TC-070: File Size Formatting**
    *   *Goal*: Verify human-readable bytes output.
    *   *Cases*: Validates correct conversion boundaries (KB vs MB formatting).
*   **TC-071 to TC-075: Code Format Regex Validation**
    *   *Goal*: Validate standard ICD-10 (International Classification of Diseases) and CPT (Current Procedural Terminology) codes.
    *   *Cases*: Rejects malformed or lowercase codes, verifies standard 5-digit CPT formats.
*   **TC-076 to TC-080: Greeting and Time-of-Day Logic**
    *   *Goal*: Match local device hour to correct greeting (Morning, Afternoon, Evening).
*   **TC-U081 to TC-U090: Security & Structure Utilities**
    *   *Goal*: Validates JWT token segment splitting, base64 email regex checks, HTML sanitizer (stripping `<script>` XSS vectors), and UUID verification.

---

### 2. 🔌 API Functional Tests (TC-001 to TC-050)
Tests standard REST API methods against the live FastAPI Backend.

*   **TC-001 to TC-010: Authentication Endpoint Verification**
    *   *Goal*: Validate endpoints `/api/auth/register` and `/api/auth/login`.
    *   *Cases*: Valid login, empty names, short passwords, duplicate emails, password validation errors.
*   **TC-011 to TC-020: User Profile Management**
    *   *Goal*: Check profile updates (`PUT /api/auth/me`).
    *   *Cases*: Verification of organization, department, and role field updates. Checks authorization rejection without bearer tokens.
*   **TC-021 to TC-030: Report Upload Capabilities**
    *   *Goal*: Verify `/api/reports/upload`.
    *   *Cases*: Valid PDF/TXT uploads, validation of report types (`radiology`, `opd`, `operative`), file size threshold checks.
*   **TC-031 to TC-040: Dashboard Stats & History API**
    *   *Goal*: Validate dashboard JSON payloads.
    *   *Cases*: Pagination checks (`?limit=X`), concurrency requests, statistics integrity.
*   **TC-041 to TC-050: Validation and Web Application Security**
    *   *Goal*: Sanitize API parameters to prevent common vulnerabilities.
    *   *Cases*: SQL Injection attempts in email/password inputs, 300-char buffer overflows, content-type header enforcement.

---

### 3. 🎨 UI/UX & Shape Validation (TC-111 to TC-130)
Ensures standard response payloads match front-end UI structures.

*   **TC-111 to TC-120: API Shape and Deployability**
    *   *Goal*: Health status validation.
    *   *Cases*: Verify response times are under 2 seconds, CORS headers allow external origins, and 422 schemas include a `"detail"` field for custom error warnings.
*   **TC-121 to TC-130: Workflow Review Queue & AI Assistant**
    *   *Goal*: Functional presence of advanced UI features.
    *   *Cases*: Reachability of `/assistant/chat` for AI coding lookup, validation checks when updating review queues with invalid IDs.

---

### 4. ⚙️ Functional E2E User Journeys (TC-F001 to TC-F060)
Tests logical sequences matching an actual user's session workflow.

*   **TC-F001 to TC-F010: User Auth Journeys**
    *   *Goal*: Verify session token state persistence.
    *   *Cases*: Ensures old tokens remain valid after a duplicate login, registers unique names and updates profile fields in sequential order.
*   **TC-F011 to TC-F020: Processing Workflow**
    *   *Goal*: Simulate report upload, processing lag, and results fetch.
*   **TC-F021 to TC-F030: Dashboard Integrity**
    *   *Goal*: Check stat consistency and rate limiting under consecutive API hits.
*   **TC-F031 to TC-F040: Role-Based Workflow Isolation**
    *   *Goal*: Verify medical reviews isolation (User A reviews remain confidential and invisible to User B).
*   **TC-F041 to TC-F050: Edge Cases & Concurrent Requests**
    *   *Goal*: Chat endpoint safety and payload resilience.
*   **TC-F051 to TC-F060: Error Handlers & CORS Checks**
    *   *Goal*: CORS preflight options headers and error handler format tests.

---

### 5. 🌐 Selenium Web Tests (TC-S001 to TC-S090)
Verifies client-side browser rendering, SPA page elements, and styles.

*   **TC-S001 to TC-S010: Basic Landing and Frame Structure**
    *   *Goal*: Ensure site resolves and displays page header.
*   **TC-S011 to TC-S020: Login Form Controls**
    *   *Goal*: Test existence of input placeholders and buttons.
*   **TC-S021 to TC-S030: Registration Screen Elements**
    *   *Goal*: Confirm role selections and navigation switches.
*   **TC-S031 to TC-S040: SPA Route Integrity**
    *   *Goal*: Test browser back/forward history persistence and refresh stability.
*   **TC-S041 to TC-S050: Dashboard Panels**
    *   *Goal*: Confirm greeting elements and logout visibility.
*   **TC-S051 to TC-S060: File Upload Screen**
    *   *Goal*: Validate drag-and-drop triggers and supported format info banners.
*   **TC-S061 to TC-S070: HTML5 & Accessibility (A11y)**
    *   *Goal*: Confirm HTML elements, button focus, color contrasts, and form labels.
*   **TC-S071 to TC-S080: Web Optimization & Network Resiliency**
    *   *Goal*: Page load limits, redirect checks, and asset loading.
*   **TC-S081 to TC-S090: Security & CSS Style Verification**
    *   *Goal*: Secure cookies check, font styles, and responsive screen shifts.

---

### 6. 📱 Appium Mobile simulated tests (TC-081 to TC-110, TC-M111 to TC-M120)
Simulates screen interactions on mobile devices (Android / iOS).

*   **TC-081 to TC-090: App Launch & Login UI**
    *   *Goal*: Confirm UI inputs are tappable and alert dialogs trigger on empty values.
*   **TC-091 to TC-100: Signup and Tab Bar Navigation**
    *   *Goal*: Tab-switching navigation stability.
*   **TC-101 to TC-110: Mobile Upload Flow**
    *   *Goal*: Verify chips selection and upload state visual indicators.
*   **TC-M111 to TC-M120: Platform Performance & Hardware Emulation**
    *   *Goal*: Check memory leaks, orientation landscape rendering, and background/foreground lifecycles.
