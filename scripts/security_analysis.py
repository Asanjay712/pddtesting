#!/usr/bin/env python3
"""
security_analysis.py
====================
Custom static security analysis for the Medical AI Platform backend.
Analyzes Python source files for common security vulnerabilities
without requiring external tools.

Findings are written to a JSON file consumed by generate_security_report.py.
"""

import ast
import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ── Finding data model ────────────────────────────────────────────────────────

@dataclass
class Finding:
    severity:    str   # CRITICAL | HIGH | MEDIUM | LOW | INFO
    vuln_type:   str
    file_path:   str
    line:        Optional[int]
    description: str
    remediation: str
    code_snippet: Optional[str] = None


findings: List[Finding] = []


def add_finding(severity, vuln_type, file_path, line, description, remediation, snippet=None):
    findings.append(Finding(
        severity=severity,
        vuln_type=vuln_type,
        file_path=file_path,
        line=line,
        description=description,
        remediation=remediation,
        code_snippet=snippet,
    ))


# ── Checks ────────────────────────────────────────────────────────────────────

def check_password_hashing(source: str, filepath: str):
    """Detect use of SHA-256 for password hashing (weak for passwords)."""
    pattern = re.compile(r'sha256.*password|password.*sha256|hashlib\.sha256', re.IGNORECASE)
    for i, line in enumerate(source.splitlines(), start=1):
        if pattern.search(line):
            add_finding(
                severity='HIGH',
                vuln_type='Weak Password Hashing (SHA-256)',
                file_path=filepath,
                line=i,
                description=(
                    'SHA-256 is a fast general-purpose hash — NOT suitable for passwords. '
                    'It is vulnerable to brute-force and rainbow table attacks.'
                ),
                remediation=(
                    'Replace hashlib.sha256 with bcrypt, argon2-id, or scrypt. '
                    'Example: `from passlib.hash import bcrypt; bcrypt.hash(password)`'
                ),
                snippet=line.strip(),
            )


def check_hardcoded_secrets(source: str, filepath: str):
    """Detect hardcoded credentials, secrets, and API keys."""
    patterns = [
        (r'SECRET_KEY\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']',        'Hardcoded JWT Secret'),
        (r'password\s*=\s*["\'][^"\']+["\']',                       'Hardcoded Password'),
        (r'API_KEY\s*=\s*["\'][^"\']+["\']',                        'Hardcoded API Key'),
        (r'postgres://[^"\']+:[^"\']+@',                             'Hardcoded DB Credentials in URL'),
        (r'postgresql\+psycopg2://[a-zA-Z0-9]+:[^@]+@',             'Hardcoded DB Password in URL'),
        (r'your_super_secret',                                        'Default/Example Secret Key'),
    ]
    for i, line in enumerate(source.splitlines(), start=1):
        for pattern, label in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip test files and config templates
                if 'test' in filepath.lower() or '.env.example' in filepath:
                    continue
                add_finding(
                    severity='CRITICAL',
                    vuln_type=f'Sensitive Data Exposure — {label}',
                    file_path=filepath,
                    line=i,
                    description=f'Potential hardcoded secret found: {label}. '
                                f'Secrets committed to source code can be extracted by anyone with repo access.',
                    remediation='Move all secrets to environment variables (.env). '
                                'Use `os.getenv("SECRET_NAME")` with no fallback default in production. '
                                'Rotate any exposed credentials immediately.',
                    snippet=re.sub(r'(password|secret|key)\s*=\s*["\'][^"\']+["\']',
                                   r'\1 = "***REDACTED***"', line.strip(), flags=re.IGNORECASE),
                )


def check_cors_wildcard(source: str, filepath: str):
    """Detect wildcard CORS allow_origins."""
    pattern = re.compile(r'allow_origins\s*=\s*\[.*["\']?\*["\']?.*\]', re.IGNORECASE)
    for i, line in enumerate(source.splitlines(), start=1):
        if pattern.search(line):
            add_finding(
                severity='MEDIUM',
                vuln_type='CORS Misconfiguration — Wildcard Origin',
                file_path=filepath,
                line=i,
                description='`allow_origins=["*"]` allows any website to make cross-origin requests '
                            'to this API, including malicious sites. Combined with credentials, this '
                            'can enable CSRF and data exfiltration.',
                remediation='Restrict CORS to known frontend origins: '
                            '`allow_origins=["https://yourdomain.com"]`. '
                            'Never combine allow_credentials=True with allow_origins=["*"].',
                snippet=line.strip(),
            )


def check_missing_rate_limiting(source: str, filepath: str):
    """Check for rate limiting on auth endpoints."""
    is_auth_router = 'login' in filepath.lower() or 'auth' in filepath.lower()
    if not is_auth_router:
        return

    has_login_route  = re.search(r'@router\.(post|get).*["\'].*login["\']', source, re.IGNORECASE)
    has_rate_limit   = re.search(r'rate.?limit|slowapi|RateLimiter|throttle|Limiter', source, re.IGNORECASE)

    if has_login_route and not has_rate_limit:
        add_finding(
            severity='HIGH',
            vuln_type='Missing Rate Limiting on Authentication',
            file_path=filepath,
            line=None,
            description='The login endpoint has no rate limiting. An attacker can perform '
                        'unlimited brute-force or credential stuffing attacks.',
            remediation='Add rate limiting using `slowapi`: '
                        '`from slowapi import Limiter; @limiter.limit("5/minute")`. '
                        'Block IPs after repeated failures.',
        )


def check_sql_injection(source: str, filepath: str):
    """Detect potential SQL injection via f-string or % formatting in queries."""
    patterns = [
        (r'execute\s*\(\s*f["\'].*{.*}.*["\']',  'f-string in SQL execute()'),
        (r'execute\s*\(\s*["\'].*%s.*["\'].*%\s', 'Old-style % formatting in SQL'),
        (r'text\s*\(\s*f["\']',                    'f-string in SQLAlchemy text()'),
    ]
    for i, line in enumerate(source.splitlines(), start=1):
        for pattern, label in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                add_finding(
                    severity='CRITICAL',
                    vuln_type=f'SQL Injection Risk — {label}',
                    file_path=filepath,
                    line=i,
                    description=f'Dynamic SQL constructed with string formatting ({label}). '
                                'If any part uses user-controlled input, this enables SQL injection.',
                    remediation='Always use parameterized queries with bound parameters: '
                                '`db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})`',
                    snippet=line.strip(),
                )


def check_jwt_issues(source: str, filepath: str):
    """Check JWT configuration for common weaknesses."""
    # Check for missing expiry
    has_create_token = 'create_token' in source or 'jwt.encode' in source
    has_exp_field    = 'exp' in source or 'expires_delta' in source or 'ACCESS_TOKEN_EXPIRE' in source

    if has_create_token and not has_exp_field:
        add_finding(
            severity='HIGH',
            vuln_type='JWT — Missing Token Expiry',
            file_path=filepath,
            line=None,
            description='JWT tokens are created without an expiration time (`exp` claim). '
                        'These tokens are valid indefinitely if compromised.',
            remediation='Always set an expiry: `{"exp": datetime.utcnow() + timedelta(hours=1)}`',
        )

    # Check for algorithm confusion
    for i, line in enumerate(source.splitlines(), start=1):
        if re.search(r'algorithm.*["\']none["\']', line, re.IGNORECASE):
            add_finding(
                severity='CRITICAL',
                vuln_type='JWT — None Algorithm Vulnerability',
                file_path=filepath,
                line=i,
                description='JWT `alg=none` disables signature verification entirely.',
                remediation='Always specify and validate the algorithm. Never allow `none`.',
                snippet=line.strip(),
            )


def check_missing_auth_on_endpoints(source: str, filepath: str):
    """Check for endpoints in protected routers that lack auth dependency."""
    # Skip non-router files
    if 'router' not in filepath.lower() and 'routes' not in filepath.lower():
        return

    # Routes that should be public (auth not required)
    public_patterns = [r'/login', r'/register', r'/forgot.password', r'/reset.password',
                       r'/health', r'root', r'startup']

    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        if re.search(r'@router\.(get|post|put|delete|patch)', line):
            # Check if the next 10 lines have auth dependency
            context = '\n'.join(lines[i-1:i+10])
            is_public = any(re.search(p, context, re.IGNORECASE) for p in public_patterns)
            has_auth  = re.search(r'verify_token|Depends\(.*token\)|get_current_user', context)

            if not is_public and not has_auth:
                route_match = re.search(r'["\']([^"\']+)["\']', line)
                route_path  = route_match.group(1) if route_match else line.strip()
                add_finding(
                    severity='MEDIUM',
                    vuln_type='Potentially Missing Authentication Check',
                    file_path=filepath,
                    line=i,
                    description=f'Endpoint `{route_path}` may lack authentication verification. '
                                'Unauthenticated users could access sensitive data.',
                    remediation='Add `token: dict = Depends(verify_token)` to the endpoint parameters.',
                    snippet=line.strip(),
                )


def check_debug_middleware(source: str, filepath: str):
    """Detect debug middleware left enabled in production code."""
    if re.search(r'DEBUG.*middleware|print.*upload.*debug|UPLOAD DEBUG', source, re.IGNORECASE):
        add_finding(
            severity='LOW',
            vuln_type='Debug Middleware Left Enabled',
            file_path=filepath,
            line=None,
            description='Debug middleware that prints request body, auth headers, and sensitive '
                        'data is present in the codebase. This may leak information in production logs.',
            remediation='Remove or disable debug middleware before production deployment. '
                        'Use environment-based toggles: `if settings.DEBUG: app.add_middleware(...)`',
        )


def check_file_upload_safety(source: str, filepath: str):
    """Check file upload endpoint for security issues."""
    if 'upload' not in filepath.lower():
        return

    has_size_limit = re.search(r'max.*size|content.length|MAX_UPLOAD|file.*size', source, re.IGNORECASE)
    has_upload     = re.search(r'UploadFile|File\(', source)

    if has_upload and not has_size_limit:
        add_finding(
            severity='MEDIUM',
            vuln_type='Missing File Upload Size Limit',
            file_path=filepath,
            line=None,
            description='File upload endpoint does not enforce a maximum file size limit. '
                        'Attackers can upload very large files to exhaust server memory/disk.',
            remediation='Add size validation: check `len(content) > MAX_FILE_SIZE` after reading. '
                        'Configure uvicorn/nginx with request size limits.',
        )

    # Check for path traversal in filename usage
    has_path_join = re.search(r'os\.path\.join.*filename|open.*filename', source, re.IGNORECASE)
    if has_path_join:
        add_finding(
            severity='HIGH',
            vuln_type='Potential Path Traversal via Filename',
            file_path=filepath,
            line=None,
            description='The uploaded filename may be used directly in filesystem operations. '
                        'A filename like `../../etc/passwd` could read arbitrary files.',
            remediation='Sanitize filenames with `werkzeug.utils.secure_filename()` or generate '
                        'a UUID-based filename and discard the original.',
        )


def check_sensitive_logging(source: str, filepath: str):
    """Detect logging of sensitive information."""
    patterns = [
        (r'log.*password', 'Password in log'),
        (r'print.*password', 'Password in print'),
        (r'log.*token', 'Token in log'),
        (r'print.*token.*=', 'Token value in print'),
    ]
    for i, line in enumerate(source.splitlines(), start=1):
        for pattern, label in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                add_finding(
                    severity='MEDIUM',
                    vuln_type=f'Sensitive Data in Logs — {label}',
                    file_path=filepath,
                    line=i,
                    description=f'Possible logging of sensitive data ({label}). '
                                'Log files may be accessible to operators or attackers.',
                    remediation='Never log passwords, tokens, or PII. '
                                'Redact sensitive fields before logging.',
                    snippet=line.strip(),
                )


# ── Runner ────────────────────────────────────────────────────────────────────

def analyze_file(filepath: str):
    """Run all checks on a single Python source file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
    except Exception as e:
        print(f"  [WARN] Could not read {filepath}: {e}")
        return

    rel_path = filepath  # keep as-is for reporting

    check_password_hashing(source, rel_path)
    check_hardcoded_secrets(source, rel_path)
    check_cors_wildcard(source, rel_path)
    check_missing_rate_limiting(source, rel_path)
    check_sql_injection(source, rel_path)
    check_jwt_issues(source, rel_path)
    check_missing_auth_on_endpoints(source, rel_path)
    check_debug_middleware(source, rel_path)
    check_file_upload_safety(source, rel_path)
    check_sensitive_logging(source, rel_path)


def main():
    parser = argparse.ArgumentParser(description='Custom security analysis for Medical AI backend')
    parser.add_argument('--backend-dir', default='backend', help='Path to backend directory')
    parser.add_argument('--output',      default='custom-analysis.json', help='Output JSON path')
    args = parser.parse_args()

    backend_path = Path(args.backend_dir)
    if not backend_path.exists():
        print(f"[ERROR] Backend directory not found: {backend_path}")
        return

    # Discover all Python files
    py_files = list(backend_path.rglob('*.py'))
    print(f"[INFO] Analyzing {len(py_files)} Python files in {backend_path}...")

    for py_file in py_files:
        if '__pycache__' in str(py_file):
            continue
        print(f"  Checking: {py_file}")
        analyze_file(str(py_file))

    # Serialize findings
    output = {
        'tool':     'custom-security-analysis',
        'version':  '1.0.0',
        'files_analyzed': len(py_files),
        'total_findings': len(findings),
        'findings': [asdict(f) for f in findings],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n[INFO] Total findings: {len(findings)}")
    severity_counts = {}
    for finding in findings:
        severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
    for sev, cnt in sorted(severity_counts.items()):
        print(f"  {sev}: {cnt}")

    print(f"[INFO] Report saved to: {out_path}")


if __name__ == '__main__':
    main()
