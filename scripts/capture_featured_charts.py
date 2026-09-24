"""Capture the live dashboard for submission; requires Playwright and local Edge."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
values = dict(line.split('=', 1) for line in (ROOT / '.env').read_text().splitlines()
              if line and not line.startswith('#') and '=' in line)
base = os.environ.get('SUPERSET_URL', 'http://localhost:8088')
target = ROOT / 'docs' / 'featured-charts.png'

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1500, 'height': 1000}, device_scale_factor=1)
    page.goto(base + '/login/', wait_until='domcontentloaded')
    page.locator('input[name="username"]').fill(values['SUPERSET_ADMIN_USERNAME'])
    page.locator('input[name="password"]').fill(values['SUPERSET_ADMIN_PASSWORD'])
    page.get_by_role('button', name='Sign In').click()
    page.goto(base + '/superset/dashboard/featured-charts/', wait_until='domcontentloaded')
    page.get_by_text('Net Revenue (THB)', exact=True).wait_for(timeout=60000)
    page.wait_for_timeout(5000)
    page.screenshot(path=str(target), full_page=True)
    browser.close()
print(f'Saved {target}')
