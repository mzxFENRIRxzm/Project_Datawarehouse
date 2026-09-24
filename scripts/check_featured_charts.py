"""Smoke test Featured Charts through Superset's HTTP API without printing credentials."""
import json
import os
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('SUPERSET_URL', 'http://localhost:8088')
values = dict(line.split('=', 1) for line in (ROOT / '.env').read_text().splitlines()
              if line and not line.startswith('#') and '=' in line)
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def call(path, method='GET', payload=None, token=None, csrf=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if csrf:
        headers['X-CSRFToken'] = csrf
    request = urllib.request.Request(BASE + path, method=method, headers=headers,
                                     data=json.dumps(payload).encode() if payload is not None else None)
    with opener.open(request, timeout=90) as response:
        return json.load(response)


auth = call('/api/v1/security/login', 'POST',
            dict(username=values['SUPERSET_ADMIN_USERNAME'], password=values['SUPERSET_ADMIN_PASSWORD'],
                 provider='db', refresh=True))
token = auth['access_token']
csrf = call('/api/v1/security/csrf_token/', token=token)['result']
dashboards = call('/api/v1/dashboard/?q=(page:0,page_size:100)', token=token)['result']
matches = [item for item in dashboards if item.get('slug') == 'featured-charts']
if len(matches) != 1:
    raise RuntimeError('Featured Charts dashboard not found')
dashboard = call(f"/api/v1/dashboard/{matches[0]['id']}", token=token)['result']
expected = {'Net Revenue (THB)', 'Orders with Sales', 'Units Sold', 'Daily Revenue',
            'Revenue by Shipper', 'Top 10 Products'}
if set(dashboard.get('charts', [])) != expected:
    raise RuntimeError(f"Dashboard chart names differ: {dashboard.get('charts')}")
listing = call('/api/v1/chart/?q=(page:0,page_size:100)', token=token)['result']
chart_ids = [chart['id'] for chart in listing if chart.get('slice_name') in expected]
if len(chart_ids) != 6:
    raise RuntimeError(f'Expected 6 charts, found {len(chart_ids)}')
for chart_id in chart_ids:
    chart = call(f'/api/v1/chart/{chart_id}', token=token)['result']
    context = chart['query_context']
    if isinstance(context, str):
        context = json.loads(context)
    result = call('/api/v1/chart/data', 'POST', context, token, csrf)
    if not result.get('result') or result['result'][0].get('error'):
        raise RuntimeError(f"Chart {chart_id} failed: {result.get('message') or result.get('result')}")
    rows = result['result'][0].get('data', [])
    if not rows:
        raise RuntimeError(f'Chart {chart_id} returned no data')
    print(f"{chart['slice_name']}: {len(rows)} result rows")
print(f"Featured Charts verified: {len(chart_ids)} charts at {BASE}/superset/dashboard/featured-charts/")
