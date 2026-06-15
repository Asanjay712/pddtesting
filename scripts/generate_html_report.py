#!/usr/bin/env python3
"""
generate_html_report.py
========================
Generates a self-contained, beautiful HTML test execution report
from JUnit XML results with embedded screenshots.
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🏥 Medical AI Platform — E2E Test Report</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
      --blue:    #2563EB;
      --green:   #22C55E;
      --red:     #EF4444;
      --amber:   #F59E0B;
      --gray-50: #F8FAFC;
      --gray-100:#F1F5F9;
      --gray-200:#E2E8F0;
      --gray-400:#94A3B8;
      --gray-700:#334155;
      --gray-900:#0F172A;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--gray-50);
      color: var(--gray-900);
      min-height: 100vh;
    }}

    header {{
      background: linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #3B82F6 100%);
      color: white;
      padding: 40px;
      text-align: center;
    }}
    header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 8px; }}
    header p  {{ opacity: 0.85; font-size: 0.95rem; }}

    .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}

    /* Stat cards */
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px;
      margin: 32px 0;
    }}
    .stat-card {{
      background: white;
      border-radius: 16px;
      padding: 24px;
      text-align: center;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
      border-top: 4px solid var(--blue);
      transition: transform .2s;
    }}
    .stat-card:hover {{ transform: translateY(-2px); }}
    .stat-card.pass  {{ border-color: var(--green); }}
    .stat-card.fail  {{ border-color: var(--red); }}
    .stat-card.skip  {{ border-color: var(--amber); }}
    .stat-card .num  {{ font-size: 2.5rem; font-weight: 700; }}
    .stat-card .label{{ color: var(--gray-400); font-size: 0.85rem; margin-top: 6px; text-transform: uppercase; letter-spacing: .05em; }}
    .stat-card.pass .num {{ color: var(--green); }}
    .stat-card.fail .num {{ color: var(--red); }}
    .stat-card.skip .num {{ color: var(--amber); }}

    /* Progress bar */
    .progress-wrap {{
      background: white;
      border-radius: 16px;
      padding: 24px 32px;
      margin-bottom: 32px;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }}
    .progress-label {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
      font-weight: 600;
    }}
    .progress-bar {{
      height: 12px;
      background: var(--gray-200);
      border-radius: 99px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      border-radius: 99px;
      background: linear-gradient(90deg, #22C55E, #16A34A);
      transition: width 1s ease;
    }}

    /* Table */
    .results-table {{
      background: white;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
      margin-bottom: 32px;
    }}
    .results-table h2 {{
      padding: 20px 24px;
      font-size: 1.1rem;
      border-bottom: 1px solid var(--gray-200);
      color: var(--gray-700);
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      background: var(--gray-50);
      padding: 14px 16px;
      text-align: left;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--gray-400);
      text-transform: uppercase;
      letter-spacing: .06em;
      border-bottom: 1px solid var(--gray-200);
    }}
    td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--gray-100);
      font-size: 0.9rem;
      vertical-align: top;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: var(--gray-50); }}

    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 99px;
      font-size: 0.78rem;
      font-weight: 600;
    }}
    .badge.pass   {{ background: #DCFCE7; color: #166534; }}
    .badge.fail   {{ background: #FEE2E2; color: #991B1B; }}
    .badge.skip   {{ background: #FEF3C7; color: #92400E; }}
    .badge.error  {{ background: #FEE2E2; color: #991B1B; }}

    .error-msg {{
      font-family: monospace;
      font-size: 0.78rem;
      color: var(--red);
      background: #FFF5F5;
      border-radius: 6px;
      padding: 6px 10px;
      margin-top: 6px;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 120px;
      overflow: auto;
    }}

    /* Screenshots */
    .screenshots {{
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
      margin-bottom: 32px;
    }}
    .screenshots h2 {{
      font-size: 1.1rem;
      color: var(--gray-700);
      margin-bottom: 16px;
    }}
    .screenshot-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
    }}
    .screenshot-item {{
      border: 1px solid var(--gray-200);
      border-radius: 12px;
      overflow: hidden;
    }}
    .screenshot-item img {{
      width: 100%;
      height: 180px;
      object-fit: cover;
    }}
    .screenshot-item p {{
      padding: 8px 12px;
      font-size: 0.75rem;
      color: var(--gray-400);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    footer {{
      text-align: center;
      padding: 32px;
      color: var(--gray-400);
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>

<header>
  <h1>🏥 Medical AI Platform</h1>
  <p>E2E Test Execution Report &nbsp;·&nbsp; {run_date} &nbsp;·&nbsp; <a href="{base_url}" style="color:rgba(255,255,255,.8)">{base_url}</a></p>
</header>

<div class="container">

  <!-- Stat cards -->
  <div class="stats">
    <div class="stat-card">
      <div class="num">{total}</div>
      <div class="label">Total Tests</div>
    </div>
    <div class="stat-card pass">
      <div class="num">{passed}</div>
      <div class="label">Passed</div>
    </div>
    <div class="stat-card fail">
      <div class="num">{failed}</div>
      <div class="label">Failed</div>
    </div>
    <div class="stat-card skip">
      <div class="num">{skipped}</div>
      <div class="label">Skipped</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--blue)">{pass_pct}%</div>
      <div class="label">Pass Rate</div>
    </div>
    <div class="stat-card">
      <div class="num" style="color:var(--gray-700);font-size:1.8rem">{duration}s</div>
      <div class="label">Duration</div>
    </div>
  </div>

  <!-- Progress bar -->
  <div class="progress-wrap">
    <div class="progress-label">
      <span>Pass Rate</span>
      <span>{pass_pct}%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" style="width:{pass_pct}%"></div>
    </div>
  </div>

  <!-- Results table -->
  <div class="results-table">
    <h2>📋 Test Results</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Test Name</th>
          <th>Suite</th>
          <th>Status</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>

  <!-- Screenshots -->
  {screenshots_section}

</div>

<footer>
  Generated by Medical AI Platform CI/CD Pipeline &nbsp;·&nbsp; Playwright E2E &nbsp;·&nbsp; {run_date}
</footer>

</body>
</html>
'''


def parse_junit(junit_path: str) -> dict:
    result = {'total':0,'passed':0,'failed':0,'skipped':0,'errors':0,'duration':0.0,'tests':[]}
    if not Path(junit_path).exists():
        return result
    try:
        root = ET.parse(junit_path).getroot()
        suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
        for suite in suites:
            for tc in suite.findall('testcase'):
                name     = tc.get('name','Unnamed')
                cls      = tc.get('classname','')
                duration = float(tc.get('time','0') or '0')
                failure  = tc.find('failure')
                error    = tc.find('error')
                skipped  = tc.find('skipped')
                if failure is not None:
                    status, msg = 'FAILED',  (failure.get('message','') or failure.text or '')[:400]
                    result['failed'] += 1
                elif error is not None:
                    status, msg = 'ERROR',   (error.get('message','')   or error.text   or '')[:400]
                    result['errors'] += 1
                elif skipped is not None:
                    status, msg = 'SKIPPED', skipped.get('message','')
                    result['skipped'] += 1
                else:
                    status, msg = 'PASSED', ''
                    result['passed'] += 1
                result['total']    += 1
                result['duration'] += duration
                result['tests'].append({'name':name,'cls':cls,'status':status,'duration':round(duration,2),'msg':msg})
    except Exception as e:
        print(f'[WARN] JUnit parse error: {e}')
    return result


def build_rows(tests: list) -> str:
    badge_class = {'PASSED':'pass','FAILED':'fail','ERROR':'fail','SKIPPED':'skip'}
    rows = []
    for i, t in enumerate(tests, 1):
        bc   = badge_class.get(t['status'], 'skip')
        err  = f'<div class="error-msg">{t["msg"]}</div>' if t['msg'] else ''
        suite= t['cls'].split('.')[-1] if t['cls'] else ''
        rows.append(f'''<tr>
          <td>{i}</td>
          <td><strong>{t["name"]}</strong>{err}</td>
          <td style="color:#94A3B8;font-size:.82rem">{suite}</td>
          <td><span class="badge {bc}">{t["status"]}</span></td>
          <td>{t["duration"]}s</td>
        </tr>''')
    return '\n'.join(rows) if rows else '<tr><td colspan="5" style="text-align:center;color:#94A3B8">No test results found</td></tr>'


def build_screenshots(screenshots_dir: str) -> str:
    pngs = list(Path(screenshots_dir).rglob('*.png')) if Path(screenshots_dir).exists() else []
    if not pngs:
        return ''
    items = []
    for p in sorted(pngs)[:20]:  # max 20 screenshots in report
        try:
            with open(p, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            items.append(f'''<div class="screenshot-item">
              <img src="data:image/png;base64,{b64}" alt="{p.name}" loading="lazy">
              <p>{p.name}</p>
            </div>''')
        except Exception:
            pass
    if not items:
        return ''
    return f'''<div class="screenshots">
      <h2>📸 Screenshots ({len(items)})</h2>
      <div class="screenshot-grid">{"".join(items)}</div>
    </div>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--junit',           default='e2e/test-results/junit.xml')
    parser.add_argument('--screenshots-dir', default='e2e/test-results')
    parser.add_argument('--output',          default='Test Results/HTML/execution-report.html')
    parser.add_argument('--base-url',        default='https://Asanjay712.github.io/pddtesting/')
    args = parser.parse_args()

    data     = parse_junit(args.junit)
    total    = data['total'] or 1
    passed   = data['passed']
    failed   = data['failed'] + data['errors']
    skipped  = data['skipped']
    pass_pct = round(passed / total * 100, 1) if total > 0 else 0
    duration = round(data['duration'], 2)
    run_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    html = HTML_TEMPLATE.format(
        run_date=run_date,
        base_url=args.base_url,
        total=data['total'],
        passed=passed,
        failed=failed,
        skipped=skipped,
        pass_pct=pass_pct,
        duration=duration,
        rows=build_rows(data['tests']),
        screenshots_section=build_screenshots(args.screenshots_dir),
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f'[INFO] HTML report saved: {out}')
    print(f'[INFO] Total={data["total"]} Passed={passed} Failed={failed} Pass%={pass_pct}')


if __name__ == '__main__':
    main()
