"""
Post-extraction field validators.
Each function returns (clean_value, is_valid). validate_record() applies all
validators to a dict and returns a cleaned copy — never raises.
"""

import re


def validate_date(val: str) -> tuple[str, bool]:
    """Normalize numeric dates to MM/DD/YYYY. Preserve month-name formats. Reject sentences."""
    if not val or str(val).strip() in ("", "Unknown", "N/A"):
        return val, False
    s = str(val).strip()
    # Reject only if it looks like a prose sentence (not a date/time string)
    is_date_like = bool(re.search(
        r'(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})'
        r'|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
        s, re.IGNORECASE
    ))
    if not is_date_like and len(s) > 30 and s.count(' ') > 3:
        return "Unknown", False
    m = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', s)
    if m:
        month, day, year = m.group(1), m.group(2), m.group(3)
        if len(year) == 2:
            year = "20" + year
        return f"{month.zfill(2)}/{day.zfill(2)}/{year}", True
    # Month-name dates kept as-is — confidence.py recognises them correctly
    return val, is_date_like


def validate_vin(val: str) -> tuple[str, bool]:
    """Require 17-char alphanumeric, no I/O/Q (standard VIN alphabet)."""
    if not val or str(val).strip() in ("", "Unknown", "N/A"):
        return val, False
    clean = str(val).strip().upper()
    if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', clean):
        return clean, True
    return "Unknown", False


def validate_report_number(val: str) -> tuple[str, bool]:
    """Reject multi-word sentences masquerading as case numbers."""
    if not val or str(val).strip() in ("", "Unknown", "N/A"):
        return val, False
    s = str(val).strip()
    if len(s.split()) > 4:
        return "Unknown", False
    if re.match(r'^[\w\-/#]{3,30}$', s):
        return s, True
    return s, len(s) <= 30


def validate_name(val: str) -> tuple[str, bool]:
    """Reject all-caps form labels that were accidentally pulled as a name."""
    if not val or str(val).strip() in ("", "Unknown", "N/A"):
        return val, False
    s = str(val).strip()
    if re.match(r'^[A-Z\s&/]+$', s) and len(s.split()) > 3:
        return "Unknown", False
    return s, True


def validate_record(record: dict, doc_type: str = "police") -> dict:
    """Apply all validators to a record; return cleaned copy."""
    r = dict(record)

    for fld in ("date_time", "inspection_date"):
        if fld in r:
            r[fld], _ = validate_date(r[fld])

    if "vin" in r:
        r["vin"], _ = validate_vin(r["vin"])

    if "report_number" in r:
        r["report_number"], _ = validate_report_number(r["report_number"])

    for fld in ("officer", "inspection_firm"):
        if fld in r:
            r[fld], _ = validate_name(r[fld])

    return r
