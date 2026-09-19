"""Run against a live Reflex app: python tests/browser_smoke.py.

Install a browser first: python -m playwright install chromium.
Artifacts go to ignored test-results/. No real Gemini API call is made.
"""
from io import BytesIO
from pathlib import Path
import re

import pandas as pd
from playwright.sync_api import sync_playwright, expect


def main():
    expect.set_options(timeout=30000)
    output = Path("test-results")
    output.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(45000)
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto("http://localhost:3000", wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="Good insights start with good data.")).to_be_visible()
        page.screenshot(path=str(output / "01-upload.png"), full_page=True)
        page.get_by_role("button", name="Try sample dataset").click()
        expect(page.get_by_role("heading", name="Meet your data.")).to_be_visible()
        expect(page.get_by_text("128", exact=True)).to_be_visible()
        page.get_by_role("button", name="Start cleaning", exact=True).click()

        def choose(label, value):
            page.get_by_text(label, exact=True).locator("..").get_by_role("combobox").click()
            page.get_by_role("option", name=value, exact=True).click()

        choose("Action", "Duplicates")
        page.get_by_role("button", name="Preview changes", exact=True).click()
        expect(page.get_by_role("heading", name="Before & after")).to_be_visible()
        expect(page.get_by_text(re.compile("128 → 120 แถว"))).to_be_visible()
        page.screenshot(path=str(output / "02-clean-preview.png"), full_page=True)
        page.get_by_role("button", name="Apply changes", exact=True).click()
        expect(page.get_by_role("heading", name="Before & after")).not_to_be_visible()
        page.get_by_role("button", name="Undo", exact=True).click()
        expect(page.get_by_text("128 rows · 8 columns", exact=True)).to_be_visible()
        page.get_by_role("button", name="Preview changes", exact=True).click()
        page.get_by_role("button", name="Apply changes", exact=True).click()
        page.get_by_role("button", name="Build dashboard", exact=True).click()
        expect(page.get_by_role("heading", name="Your data, in perspective.")).to_be_visible()
        expect(page.locator(".js-plotly-plot").first).to_be_visible()
        page.screenshot(path=str(output / "03-dashboard.png"), full_page=True)
        choose("Category", "category")
        choose("Category value", "Software")
        page.get_by_role("button", name="Apply filters", exact=True).click()
        expect(page.get_by_text("category = Software", exact=True)).to_be_visible()
        page.get_by_role("button", name="Reset filters", exact=True).click()
        expect(page.get_by_text("All rows · ไม่ใช้ตัวกรอง", exact=True)).to_be_visible()
        choose("X axis", "category")
        choose("Y axis · numeric", "revenue")
        page.get_by_role("button", name="Create chart", exact=True).click()
        expect(page.get_by_text("revenue by category · Sum", exact=True)).to_be_visible()
        page.get_by_role("button", name="Generate insights", exact=True).click()
        expect(page.get_by_text(re.compile("ยังไม่ได้ตั้งค่า GEMINI_API_KEY"))).to_be_visible()
        page.get_by_role("button", name="Export results", exact=True).click()
        expect(page.get_by_role("heading", name="Ready for what comes next.")).to_be_visible()
        for title, suffix in [("Download CSV", ".csv"), ("Download Excel", ".xlsx"), ("Download PDF", ".pdf")]:
            with page.expect_download(timeout=90000) as info:
                page.get_by_role("button", name=title, exact=True).click()
            download = info.value
            path = output / download.suggested_filename
            download.save_as(path)
            assert path.suffix == suffix
            if suffix == ".csv":
                assert len(pd.read_csv(path)) == 120
            elif suffix == ".xlsx":
                assert len(pd.read_excel(path)) == 120
            else:
                assert path.read_bytes().startswith(b"%PDF")
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(output / "04-mobile.png"), full_page=True)
        page.get_by_role("button", name=re.compile("^Upload")).click()
        page.locator('input[type="file"]').set_input_files({"name": "small.csv", "mimeType": "text/csv", "buffer": b"name,value\nAda,10\nLin,20\n"})
        page.get_by_role("button", name="Upload & profile", exact=True).click()
        expect(page.get_by_role("heading", name="Meet your data.")).to_be_visible()
        expect(page.get_by_text("small.csv", exact=True)).to_be_visible()
        assert not errors, errors
        context.close()
        browser.close()
    print("Browser workflow passed: sample, preview/apply/undo, charts, filters, AI fallback, CSV/Excel/PDF and upload.")


if __name__ == "__main__":
    main()
