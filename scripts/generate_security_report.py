#!/usr/bin/env python3
"""
generate_security_report.py
============================
Merges findings from Semgrep, Trivy, pip-audit, and custom analysis
into a single, beautifully formatted Markdown security report.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict


SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4, 'UNKNOWN': 5}
SEVERITY_EMOJI = {
    'CRITICAL': '🔴',
    'HIGH':     '🟠',
    'MEDIUM':   '🟡',
    'LOW':      '🔵',
    'INFO':     '⚪',
    'UNKNOWN':  '⚫',
}


def load_json_safe(path: str) -> dict:
    """Load JSON file, return empty dict if not found or invalid."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def parse_semgrep(data: dict) -> list:
    """Parse Semgrep JSON output into normalized finding dicts."""
    results = []
    for r in data.get('results', []):
        sev = r.get('extra', {}).get('severity', 'MEDIUM').upper()
        if sev == 'WARNING':
            sev = 'MEDIUM'
        if sev == 'ERROR':
            sev = 'HIGH'
        results.append({
            'severity':    sev,
            'vuln_type':   r.get('check_id', 'Semgrep Finding').split('.')[-1].replace('-', ' ').title(),
            'file_path':   r.get('path', 'unknown'),
            'line':        r.get('start', {}).get('line'),
            'description': r.get('extra', {}).get('message', 'See Semgrep rule for details.'),
            'remediation': r.get('extra', {}).get('fix', 'Review Semgrep rule documentation.'),
            'source':      'Semgrep',
        })
    return results


def parse_trivy(data: dict) -> list:
    """Parse Trivy JSON output into normalized finding dicts."""
    results = []
    for result in data.get('Results', []):
        for vuln in result.get('Vulnerabilities', []):
            sev = vuln.get('Severity', 'UNKNOWN').upper()
            pkg = vuln.get('PkgName', 'unknown')
            cve = vuln.get('VulnerabilityID', '')
            fixed = vuln.get('FixedVersion', 'No fix available')
            results.append({
                'severity':    sev,
                'vuln_type':   f'CVE in Dependency: {pkg}',
                'file_path':   result.get('Target', 'requirements.txt'),
                'line':        None,
                'description': (
                    f'**{cve}** — {vuln.get("Title", "No title")}. '
                    f'Installed: `{vuln.get("InstalledVersion", "unknown")}`. '
                    f'{vuln.get("Description", "")[:300]}'
                ),
                'remediation': f'Upgrade `{pkg}` to version `{fixed}`.',
                'source':      'Trivy',
            })
    return results


def parse_pip_audit(data) -> list:
    """Parse pip-audit JSON output."""
    results = []
    # pip-audit can return a list or dict
    items = data if isinstance(data, list) else data.get('dependencies', [])
    for dep in items:
        for vuln in dep.get('vulns', []):
            results.append({
                'severity':    'HIGH',
                'vuln_type':   f'Known Vulnerability in {dep.get("name", "?")}',
                'file_path':   'backend/requirements.txt',
                'line':        None,
                'description': (
                    f'**{vuln.get("id", "?")}**: {vuln.get("description", "")} '
                    f'(version `{dep.get("version", "?")}` is affected)'
                ),
                'remediation': f'Upgrade to a fixed version: {", ".join(vuln.get("fix_versions", ["check PyPI"]))}',
                'source':      'pip-audit',
            })
    return results


def parse_custom(data: dict) -> list:
    """Parse custom analysis findings."""
    results = []
    for f in data.get('findings', []):
        results.append({
            'severity':    f.get('severity', 'MEDIUM'),
            'vuln_type':   f.get('vuln_type', 'Security Issue'),
            'file_path':   f.get('file_path', 'unknown'),
            'line':        f.get('line'),
            'description': f.get('description', ''),
            'remediation': f.get('remediation', ''),
            'code_snippet': f.get('code_snippet'),
            'source':      'Custom Analysis',
        })
    return results


def count_by_severity(findings: list) -> dict:
    counts = defaultdict(int)
    for f in findings:
        counts[f['severity']] += 1
    return dict(counts)


def generate_report(all_findings: list, output_path: str):
    """Render the final Markdown security report."""
    counts    = count_by_severity(all_findings)
    total     = len(all_findings)
    critical  = counts.get('CRITICAL', 0)
    high      = counts.get('HIGH', 0)
    medium    = counts.get('MEDIUM', 0)
    low       = counts.get('LOW', 0)
    info      = counts.get('INFO', 0)

    # Sort findings by severity
    sorted_findings = sorted(
        all_findings,
        key=lambda x: SEVERITY_ORDER.get(x.get('severity', 'UNKNOWN'), 99)
    )

    # Identify top risks
    top_risks = []
    if any('SHA-256' in f.get('vuln_type', '') or 'Weak Password' in f.get('vuln_type', '')
           for f in all_findings):
        top_risks.append('Weak SHA-256 password hashing — upgrade to bcrypt/argon2')
    if any('CORS' in f.get('vuln_type', '') for f in all_findings):
        top_risks.append('Wildcard CORS configuration — restrict to known origins')
    if any('Rate Limiting' in f.get('vuln_type', '') for f in all_findings):
        top_risks.append('No rate limiting on auth endpoints — enables brute force attacks')
    if any('SQL Injection' in f.get('vuln_type', '') for f in all_findings):
        top_risks.append('Potential SQL injection via dynamic query construction')
    if any('Hardcoded' in f.get('vuln_type', '') or 'Default' in f.get('vuln_type', '')
           for f in all_findings):
        top_risks.append('Hardcoded or default secrets in source code')
    if any('File Upload' in f.get('vuln_type', '') for f in all_findings):
        top_risks.append('File upload endpoint lacks size limits — DoS risk')
    if any('Authentication' in f.get('vuln_type', '') for f in all_findings):
        top_risks.append('Endpoints potentially missing authentication checks (IDOR risk)')
    if not top_risks:
        top_risks.append('No critical risks identified in this scan')

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    lines = []
    lines.append('# 🔒 Security Review Report')
    lines.append(f'\n**Generated:** {now}  ')
    lines.append('**Project:** Medical AI Platform — `Asanjay712/pddtesting`  ')
    lines.append('**Tools:** Semgrep · Trivy · pip-audit · Custom Analysis\n')
    lines.append('---\n')

    # Executive Summary
    lines.append('## 📋 Executive Summary\n')
    lines.append('| Severity | Count |')
    lines.append('|---|---|')
    lines.append(f'| 🔴 Critical | **{critical}** |')
    lines.append(f'| 🟠 High     | **{high}** |')
    lines.append(f'| 🟡 Medium   | **{medium}** |')
    lines.append(f'| 🔵 Low      | **{low}** |')
    lines.append(f'| ⚪ Info     | **{info}** |')
    lines.append(f'| **Total**  | **{total}** |')
    lines.append('')
    lines.append('### Most Important Risks\n')
    for risk in top_risks[:6]:
        lines.append(f'- {risk}')
    lines.append('\n---\n')

    # Findings by severity group
    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
        group = [f for f in sorted_findings if f.get('severity', '').upper() == sev]
        if not group:
            continue

        emoji = SEVERITY_EMOJI.get(sev, '⚫')
        lines.append(f'## {emoji} {sev} Findings ({len(group)})\n')

        for idx, finding in enumerate(group, start=1):
            file_path = finding.get('file_path', 'unknown')
            line_num  = finding.get('line')
            location  = f'`{file_path}`' + (f' line {line_num}' if line_num else '')
            source    = finding.get('source', '')

            lines.append(f'### {idx}. {finding.get("vuln_type", "Finding")}')
            lines.append(f'\n**Source:** {source}  ')
            lines.append(f'**Location:** {location}  ')
            lines.append(f'**Severity:** {emoji} {sev}\n')
            lines.append(f'**Description:**  ')
            lines.append(f'{finding.get("description", "")}\n')

            snippet = finding.get('code_snippet')
            if snippet:
                lines.append('**Code:**')
                lines.append(f'```python\n{snippet}\n```\n')

            lines.append(f'**Remediation:**  ')
            lines.append(f'{finding.get("remediation", "")}\n')
            lines.append('---\n')

    # Endpoint analysis summary
    lines.append('## 🔍 Endpoint Security Analysis\n')
    lines.append('| Endpoint | Auth Required | Rate Limited | Notes |')
    lines.append('|---|---|---|---|')
    endpoints = [
        ('POST /api/auth/register',       '❌ No',  '❌ No',  'Public registration — consider CAPTCHA'),
        ('POST /api/auth/login',           '❌ No',  '❌ No',  '⚠️ Brute force risk — add rate limiting'),
        ('GET  /api/auth/me',              '✅ JWT', '❌ No',  'OK'),
        ('PUT  /api/auth/me',              '✅ JWT', '❌ No',  'OK'),
        ('POST /api/auth/forgot-password', '❌ No',  '❌ No',  '⚠️ OTP enumeration risk'),
        ('POST /api/auth/reset-password',  '❌ No',  '❌ No',  'OK if OTP expiry is enforced'),
        ('POST /api/upload',               '⚠️ Optional', '❌ No', '⚠️ No auth required — any user can upload'),
        ('GET  /api/reports/history',      '⚠️ Optional', '❌ No', 'Returns all reports if no user_id'),
        ('GET  /api/reports/alerts',       '⚠️ Optional', '❌ No', 'May expose other users\' alerts'),
        ('GET  /api/reports/{id}/results', '❌ No',  '❌ No',  '⚠️ IDOR — any report ID can be accessed'),
        ('POST /api/alerts/{id}/resolve',  '❌ No',  '❌ No',  '⚠️ No auth — anyone can resolve alerts'),
        ('GET  /health',                   '❌ No',  '❌ No',  'OK — health checks should be public'),
    ]
    for ep in endpoints:
        lines.append(f'| `{ep[0]}` | {ep[1]} | {ep[2]} | {ep[3]} |')

    lines.append('\n---\n')
    lines.append('## 📌 Recommendations Priority Order\n')
    lines.append('1. **[CRITICAL]** Replace SHA-256 with bcrypt for password hashing')
    lines.append('2. **[CRITICAL]** Move all secrets to environment variables; remove defaults')
    lines.append('3. **[HIGH]** Add rate limiting to `/login` and `/forgot-password` endpoints')
    lines.append('4. **[HIGH]** Require authentication on `/api/upload` and `/api/reports/{id}/resolve`')
    lines.append('5. **[HIGH]** Fix IDOR on `GET /api/reports/{id}/results` — verify ownership')
    lines.append('6. **[MEDIUM]** Restrict CORS to your specific frontend domain')
    lines.append('7. **[MEDIUM]** Add file upload size limits (e.g., 10 MB max)')
    lines.append('8. **[MEDIUM]** Remove debug middleware before production deployment')
    lines.append('9. **[LOW]**  Add request logging with sensitive field redaction')
    lines.append('10. **[LOW]** Consider adding security headers (HSTS, CSP, X-Frame-Options)')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'[INFO] Security report written to: {output_path}')
    print(f'[INFO] Total: {total} | Critical: {critical} | High: {high} | Medium: {medium} | Low: {low}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--semgrep',   default='')
    parser.add_argument('--trivy',     default='')
    parser.add_argument('--pip-audit', default='')
    parser.add_argument('--custom',    default='')
    parser.add_argument('--output',    default='Vulnerability Test Results/security-review.md')
    args = parser.parse_args()

    all_findings = []

    if args.semgrep and Path(args.semgrep).exists():
        data = load_json_safe(args.semgrep)
        parsed = parse_semgrep(data)
        print(f'[INFO] Semgrep: {len(parsed)} findings')
        all_findings.extend(parsed)

    if args.trivy and Path(args.trivy).exists():
        data = load_json_safe(args.trivy)
        parsed = parse_trivy(data)
        print(f'[INFO] Trivy: {len(parsed)} findings')
        all_findings.extend(parsed)

    pip_audit_arg = getattr(args, 'pip_audit', '') or ''
    if pip_audit_arg and Path(pip_audit_arg).exists():
        data = load_json_safe(pip_audit_arg)
        parsed = parse_pip_audit(data)
        print(f'[INFO] pip-audit: {len(parsed)} findings')
        all_findings.extend(parsed)

    if args.custom and Path(args.custom).exists():
        data = load_json_safe(args.custom)
        parsed = parse_custom(data)
        print(f'[INFO] Custom analysis: {len(parsed)} findings')
        all_findings.extend(parsed)

    if not all_findings:
        print('[WARN] No findings from any tool — generating empty report')
        all_findings = [{
            'severity':    'INFO',
            'vuln_type':   'Scan Complete',
            'file_path':   'N/A',
            'line':        None,
            'description': 'No findings were produced by the security tools. '
                           'This may indicate tools did not run or produced no output.',
            'remediation': 'Review CI logs to ensure all tools executed correctly.',
            'source':      'System',
        }]

    generate_report(all_findings, args.output)


if __name__ == '__main__':
    main()
