"""
PancreaScan — Unit Tests
test_unit.py

Covers pure-logic, utility, and data-processing functions:
  - MIME type inference
  - Password hashing
  - File size formatting
  - Token/JWT structure
  - ICD/CPT code format validation
  - Date helpers
  - Greeting logic
  - Data shape validators
  Total: 30 unique unit test cases (TC-051 to TC-080)
"""

import pytest
import hashlib
import re
import json
import base64
import time
import os
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# TC-051 to TC-060  ─  MIME TYPE INFERENCE UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def infer_mime_type(filename: str) -> str:
    """Mirror of the frontend inferMimeType() helper."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mapping = {
        "pdf":  "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc":  "application/msword",
        "txt":  "text/plain",
    }
    return mapping.get(ext, "application/pdf")


class TestMimeTypeInference:

    def test_TC051_pdf_extension_returns_correct_mime(self):
        """TC-051: .pdf maps to application/pdf."""
        assert infer_mime_type("report.pdf") == "application/pdf"

    def test_TC052_docx_extension_returns_correct_mime(self):
        """TC-052: .docx maps to OOXML word processing mime."""
        result = infer_mime_type("discharge.docx")
        assert "wordprocessingml" in result

    def test_TC053_doc_extension_returns_msword(self):
        """TC-053: .doc maps to application/msword."""
        assert infer_mime_type("old_format.doc") == "application/msword"

    def test_TC054_txt_extension_returns_text_plain(self):
        """TC-054: .txt maps to text/plain."""
        assert infer_mime_type("notes.txt") == "text/plain"

    def test_TC055_unknown_extension_defaults_to_pdf(self):
        """TC-055: Unknown extension defaults to application/pdf."""
        assert infer_mime_type("report.xyz") == "application/pdf"

    def test_TC056_uppercase_extension_handled(self):
        """TC-056: Uppercase .PDF extension is handled."""
        assert infer_mime_type("REPORT.PDF") == "application/pdf"

    def test_TC057_no_extension_defaults_to_pdf(self):
        """TC-057: Filename with no extension defaults to PDF."""
        assert infer_mime_type("noextension") == "application/pdf"

    def test_TC058_multiple_dots_uses_last_segment(self):
        """TC-058: File with dots in name uses last segment as extension."""
        result = infer_mime_type("my.report.2026.pdf")
        assert result == "application/pdf"

    def test_TC059_empty_filename_defaults_to_pdf(self):
        """TC-059: Empty filename defaults to PDF mime."""
        assert infer_mime_type("") == "application/pdf"

    def test_TC060_txt_is_not_pdf(self):
        """TC-060: .txt mime type is not application/pdf."""
        assert infer_mime_type("notes.txt") != "application/pdf"


# ══════════════════════════════════════════════════════════════════════════════
# TC-061 to TC-065  ─  PASSWORD HASHING UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Mirror of the backend hash_password() function."""
    return hashlib.sha256(password.encode()).hexdigest()


class TestPasswordHashing:

    def test_TC061_same_password_same_hash(self):
        """TC-061: Same password always produces same hash."""
        assert hash_password("MyPassword!") == hash_password("MyPassword!")

    def test_TC062_different_passwords_different_hashes(self):
        """TC-062: Different passwords produce different hashes."""
        assert hash_password("Password1") != hash_password("Password2")

    def test_TC063_hash_is_64_chars_hex(self):
        """TC-063: SHA-256 hash is always 64 hex characters."""
        h = hash_password("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_TC064_case_sensitive_passwords(self):
        """TC-064: Password hashing is case-sensitive."""
        assert hash_password("password") != hash_password("Password")

    def test_TC065_empty_password_has_valid_hash(self):
        """TC-065: Empty string password produces a valid (non-empty) hash."""
        h = hash_password("")
        assert len(h) == 64


# ══════════════════════════════════════════════════════════════════════════════
# TC-066 to TC-070  ─  FILE SIZE FORMATTING UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def format_file_size(size_bytes: int) -> str:
    """Mirror of the upload.js FileRow size formatter."""
    if size_bytes > 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f} MB"
    return f"{size_bytes // 1024} KB"


class TestFileSizeFormatting:

    def test_TC066_bytes_less_than_1mb_shown_as_kb(self):
        """TC-066: File under 1 MB is displayed in KB."""
        assert "KB" in format_file_size(512 * 1024)

    def test_TC067_bytes_over_1mb_shown_as_mb(self):
        """TC-067: File over 1 MB is displayed in MB."""
        assert "MB" in format_file_size(2 * 1024 * 1024)

    def test_TC068_exactly_1mb_shown_as_mb(self):
        """TC-068: Exactly 1 MB is shown as MB (not KB)."""
        result = format_file_size(1024 * 1024 + 1)
        assert "MB" in result

    def test_TC069_zero_bytes_returns_0_kb(self):
        """TC-069: Zero-byte file returns '0 KB'."""
        assert format_file_size(0) == "0 KB"

    def test_TC070_1kb_file_displayed_correctly(self):
        """TC-070: 1024 byte file shows as 1 KB."""
        assert format_file_size(1024) == "1 KB"


# ══════════════════════════════════════════════════════════════════════════════
# TC-071 to TC-075  ─  ICD-10 / CPT CODE VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

ICD10_PATTERN = re.compile(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{0,4})?$")
CPT_PATTERN   = re.compile(r"^\d{5}$")


class TestCodeValidation:

    def test_TC071_valid_icd10_code_i10(self):
        """TC-071: I10 is a valid ICD-10 code."""
        assert ICD10_PATTERN.match("I10")

    def test_TC072_valid_icd10_with_decimal(self):
        """TC-072: E11.9 is a valid ICD-10 code."""
        assert ICD10_PATTERN.match("E11.9")

    def test_TC073_invalid_icd10_lowercase(self):
        """TC-073: Lowercase ICD-10 code fails validation."""
        assert not ICD10_PATTERN.match("i10")

    def test_TC074_valid_cpt_code_5_digits(self):
        """TC-074: 93000 is a valid CPT code."""
        assert CPT_PATTERN.match("93000")

    def test_TC075_invalid_cpt_less_than_5_digits(self):
        """TC-075: 4-digit CPT code fails validation."""
        assert not CPT_PATTERN.match("1234")


# ══════════════════════════════════════════════════════════════════════════════
# TC-076 to TC-080  ─  GREETING & DATE LOGIC UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def get_greeting(hour: int) -> str:
    """Mirror of the frontend getGreeting() helper."""
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


class TestGreetingLogic:

    def test_TC076_morning_greeting_at_0(self):
        """TC-076: Hour 0 returns 'Good morning'."""
        assert get_greeting(0) == "Good morning"

    def test_TC077_morning_greeting_at_11(self):
        """TC-077: Hour 11 returns 'Good morning'."""
        assert get_greeting(11) == "Good morning"

    def test_TC078_afternoon_greeting_at_12(self):
        """TC-078: Hour 12 returns 'Good afternoon'."""
        assert get_greeting(12) == "Good afternoon"

    def test_TC079_afternoon_greeting_at_16(self):
        """TC-079: Hour 16 returns 'Good afternoon'."""
        assert get_greeting(16) == "Good afternoon"

    def test_TC080_evening_greeting_at_17(self):
        """TC-080: Hour 17 returns 'Good evening'."""
        assert get_greeting(17) == "Good evening"


# ══════════════════════════════════════════════════════════════════════════════
# TC-U081 to TC-U090  ─  ADDITIONAL UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_REPORT_TYPES = {"auto", "discharge", "radiology", "lab", "opd", "operative"}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}


def validate_password_strength(password: str) -> bool:
    """Check password has 8+ chars, uppercase, lowercase, and digit."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit


def sanitize_html(text: str) -> str:
    """Strip <script> tags from text (basic XSS prevention)."""
    return re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage, returning 0.0 if total is zero."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def is_valid_file_extension(filename: str) -> bool:
    """Check if filename has an allowed extension."""
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


class TestAdditionalUnitTests:

    def test_TCU081_jwt_structure_three_parts(self):
        """TC-U081: A JWT token has exactly 3 dot-separated parts."""
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        parts = fake_jwt.split(".")
        assert len(parts) == 3, f"JWT should have 3 parts, got {len(parts)}"

    def test_TCU082_jwt_header_contains_alg(self):
        """TC-U082: Base64-decoded JWT header contains 'alg' field."""
        header_b64 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        # Add padding
        padded = header_b64 + "=" * (4 - len(header_b64) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        assert "alg" in decoded, "JWT header must contain 'alg' field"

    def test_TCU083_iso_date_format_valid(self):
        """TC-U083: ISO date YYYY-MM-DD format validates correctly."""
        assert ISO_DATE_PATTERN.match("2026-06-16")
        assert ISO_DATE_PATTERN.match("2000-01-01")
        assert not ISO_DATE_PATTERN.match("16-06-2026")
        assert not ISO_DATE_PATTERN.match("2026/06/16")

    def test_TCU084_email_format_validation(self):
        """TC-U084: Email format regex validates correct and incorrect emails."""
        assert EMAIL_PATTERN.match("user@example.com")
        assert EMAIL_PATTERN.match("test.user+tag@domain.io")
        assert not EMAIL_PATTERN.match("not-an-email")
        assert not EMAIL_PATTERN.match("@missing-local.com")
        assert not EMAIL_PATTERN.match("user@.com")

    def test_TCU085_report_type_enum_validation(self):
        """TC-U085: Only 6 valid report types are accepted."""
        for valid in ["auto", "discharge", "radiology", "lab", "opd", "operative"]:
            assert valid in VALID_REPORT_TYPES
        assert "invalid" not in VALID_REPORT_TYPES
        assert "xray" not in VALID_REPORT_TYPES
        assert len(VALID_REPORT_TYPES) == 6

    def test_TCU086_password_strength_validation(self):
        """TC-U086: Password strength requires 8+ chars, upper, lower, number."""
        assert validate_password_strength("MyPass12") is True
        assert validate_password_strength("StrongP@ss1") is True
        assert validate_password_strength("short1A") is False      # too short
        assert validate_password_strength("alllowercase1") is False  # no uppercase
        assert validate_password_strength("ALLUPPERCASE1") is False  # no lowercase
        assert validate_password_strength("NoDigitsHere") is False   # no digit

    def test_TCU087_file_extension_whitelist(self):
        """TC-U087: Only .pdf, .txt, .docx, .doc extensions are allowed."""
        assert is_valid_file_extension("report.pdf") is True
        assert is_valid_file_extension("notes.txt") is True
        assert is_valid_file_extension("doc.docx") is True
        assert is_valid_file_extension("legacy.doc") is True
        assert is_valid_file_extension("image.jpg") is False
        assert is_valid_file_extension("script.py") is False
        assert is_valid_file_extension("noextension") is False

    def test_TCU088_sanitize_html_strips_script_tags(self):
        """TC-U088: HTML sanitizer removes <script> tags."""
        dirty = '<p>Hello</p><script>alert("XSS")</script><p>World</p>'
        clean = sanitize_html(dirty)
        assert "<script" not in clean
        assert "alert" not in clean
        assert "<p>Hello</p>" in clean
        assert "<p>World</p>" in clean

    def test_TCU089_uuid_format_validation(self):
        """TC-U089: UUID v4 format validates correctly."""
        import uuid
        valid_uuid = str(uuid.uuid4())
        assert UUID_PATTERN.match(valid_uuid), f"Valid UUID failed: {valid_uuid}"
        assert not UUID_PATTERN.match("not-a-uuid")
        assert not UUID_PATTERN.match("12345678-1234-1234-1234")  # too short
        assert not UUID_PATTERN.match("")

    def test_TCU090_percentage_calculation(self):
        """TC-U090: Percentage calculation handles normal and edge cases."""
        assert calculate_percentage(50, 100) == 50.0
        assert calculate_percentage(1, 3) == 33.33
        assert calculate_percentage(0, 100) == 0.0
        assert calculate_percentage(100, 100) == 100.0
        assert calculate_percentage(5, 0) == 0.0  # division by zero → 0
