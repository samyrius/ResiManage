"""Minimal browser smoke checks for the ResiManage login screen.

Run against a disposable CI instance only:
    RESIMANAGE_BASE_URL=http://127.0.0.1:5000 pytest -q tests/e2e/browser_smoke.py
"""
import os

import pytest
from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("RESIMANAGE_BASE_URL", "http://127.0.0.1:5000").rstrip("/")


def test_login_screen_renders_in_real_browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            response = page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            assert response is not None
            assert response.status == 200
            assert page.locator('input[type="password"]').count() >= 1
            assert page.locator("form").count() >= 1
        finally:
            browser.close()
