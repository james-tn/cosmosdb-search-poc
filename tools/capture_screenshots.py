"""Capture screenshots of the running Streamlit app for the docs.

Prereq: the app must be running (e.g. `python -m streamlit run app.py`) and
Playwright chromium installed (`pip install playwright && playwright install chromium`).

Usage:  python tools/capture_screenshots.py [base_url]
Writes PNGs to docs/img/.
"""
from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "img")
os.makedirs(OUT, exist_ok=True)


def settle(page, secs=2.5):
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    for _ in range(40):
        if page.locator('[data-testid="stStatusWidget"]').count() == 0:
            break
        time.sleep(0.25)
    time.sleep(secs)


def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print("saved", os.path.relpath(path))


def click_text(page, text):
    page.get_by_text(text, exact=False).first.click()
    settle(page)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1500, "height": 1000},
                                device_scale_factor=2)
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_selector("h1", timeout=30000)
        settle(page, 3)
        shot(page, "01-search-explorer.png")

        try:
            page.get_by_text("Compare all three", exact=False).first.click()
            settle(page, 3)
            shot(page, "02-compare.png")
            page.get_by_text("Compare all three", exact=False).first.click()
            settle(page)
        except Exception as e:
            print("compare shot skipped:", str(e)[:100])

        try:
            click_text(page, "Analytics (facets)")
            shot(page, "03-analytics.png")
        except Exception as e:
            print("analytics shot skipped:", str(e)[:100])

        try:
            click_text(page, "Ask Copilot (RAG)")
            page.get_by_role("button", name="Ask").first.click()
            for _ in range(60):
                if page.get_by_text("Answer", exact=False).count() > 0:
                    break
                time.sleep(0.5)
            settle(page, 3)
            shot(page, "04-agent.png")
        except Exception as e:
            print("agent shot skipped:", str(e)[:100])

        browser.close()


if __name__ == "__main__":
    main()
