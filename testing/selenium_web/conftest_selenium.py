"""
PancreaScan — Selenium Web Tests
conftest_selenium.py — Headless Chrome driver fixtures and helpers

Targets the Expo/React-Native web app deployed on GitHub Pages:
  https://Tilaksai99.github.io/pddtesting
  (or SELENIUM_BASE_URL env var)

Falls back gracefully when the URL is unreachable.
"""

import pytest
import os
import socket
import urllib.request
from urllib.error import URLError

# ── Target URL ─────────────────────────────────────────────────────────────────
SELENIUM_BASE_URL = os.getenv(
    "SELENIUM_BASE_URL",
    "https://pddtesting-gpxnq9k79-teamx2411.vercel.app"
).rstrip("/")


# ── Reachability check (done once at import time) ──────────────────────────────
def _site_reachable(url: str, timeout: int = 10) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


SITE_LIVE = _site_reachable(SELENIUM_BASE_URL)


# ── Selenium availability check ────────────────────────────────────────────────
def _selenium_available() -> bool:
    try:
        import selenium  # noqa: F401
        return True
    except ImportError:
        return False


SELENIUM_READY = _selenium_available()


# ── Chrome driver fixture (session-scoped for speed) ──────────────────────────
@pytest.fixture(scope="session")
def driver():
    """
    Provides a headless Chrome WebDriver for the test session.
    Skips the entire session if Selenium is not installed or site is unreachable.
    """
    if not SELENIUM_READY:
        pytest.skip("selenium package not installed — run: pip install selenium webdriver-manager")

    if not SITE_LIVE:
        pytest.skip(
            f"Target site unreachable: {SELENIUM_BASE_URL}\n"
            "Set SELENIUM_BASE_URL env var to a running instance."
        )

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    try:
        # Try webdriver-manager first
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        drv = webdriver.Chrome(service=service, options=options)
    except Exception:
        # Fall back to system chromedriver
        try:
            drv = webdriver.Chrome(options=options)
        except Exception as e:
            pytest.skip(f"Could not launch Chrome WebDriver: {e}")

    drv.set_page_load_timeout(30)
    drv.implicitly_wait(5)

    yield drv

    drv.quit()


# ── Page fixture ───────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def base_url():
    return SELENIUM_BASE_URL


@pytest.fixture(scope="session")
def home_page(driver, base_url):
    """Navigate to home page once per session and return driver."""
    driver.get(base_url)
    return driver


# ── Helper utilities exposed as fixtures ───────────────────────────────────────
@pytest.fixture(scope="session")
def wait(driver):
    """Returns a configured WebDriverWait instance."""
    from selenium.webdriver.support.ui import WebDriverWait
    return WebDriverWait(driver, timeout=15)
