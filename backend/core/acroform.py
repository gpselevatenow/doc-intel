"""
AcroForm field extraction via pdfminer.six (bundled with pdfplumber).
Used to read digitally filled checkboxes that Docling cannot capture —
primarily weather and accident_type on HSMV forms.
"""

import re


def extract_acroform_fields(pdf_path: str) -> dict[str, str]:
    """
    Extract all AcroForm widget values from a PDF.
    Returns {field_name: value}. Empty dict if no AcroForm or on any error.
    Checkbox values are '/Yes', '/On', '/Off', or similar PDF name objects.
    """
    try:
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        from pdfminer.pdftypes import resolve1
    except ImportError:
        return {}

    def _decode(v) -> str:
        if isinstance(v, bytes):
            return v.decode("utf-8", errors="replace")
        if hasattr(v, "name"):          # PSLiteral / PDFName
            return "/" + v.name if not str(v).startswith("/") else str(v)
        return str(v) if v is not None else ""

    fields: dict[str, str] = {}

    def _walk(obj):
        obj = resolve1(obj)
        if not isinstance(obj, dict):
            return
        name = _decode(obj.get("/T", ""))
        value = _decode(obj.get("/V", ""))
        kids = obj.get("/Kids", [])
        if kids:
            for kid in kids:
                _walk(kid)
        elif name:
            fields[name] = value

    try:
        with open(pdf_path, "rb") as f:
            parser = PDFParser(f)
            doc = PDFDocument(parser)
            if "/AcroForm" not in doc.catalog:
                return {}
            acroform = resolve1(doc.catalog["/AcroForm"])
            for field_ref in acroform.get("/Fields", []):
                _walk(field_ref)
    except Exception:
        return {}

    return fields


# ── HSMV checkbox mappings ────────────────────────────────────────────────────

_WEATHER_KEYWORDS = {
    "clear": "Clear",
    "cloudy": "Cloudy",
    "rain": "Rain",
    "fog": "Fog / Smog / Smoke",
    "sleet": "Sleet / Hail",
    "wind": "High Winds",
    "blowing": "Blowing Sand / Soil / Dirt",
    "other": "Other",
}

_ACCIDENT_KEYWORDS = {
    "angle": "Angle",
    "head": "Head-On",
    "rear": "Rear-End",
    "same": "Sideswipe Same Direction",
    "opposite": "Sideswipe Opposite Direction",
    "single": "Single Vehicle",
    "backing": "Backing",
}

_CHECKED = {"/yes", "/on", "yes", "on", "1", "true"}


def _first_checked(fields: dict, hint: str, keyword_map: dict) -> str | None:
    """
    Scan fields whose name contains `hint`.
    Return the canonical label for the first checked box.
    """
    for name, val in fields.items():
        lower_name = name.lower().replace(" ", "_").replace("-", "_")
        if hint not in lower_name:
            continue
        if val.lower().lstrip("/") in _CHECKED or val.lower() in _CHECKED:
            for kw, label in keyword_map.items():
                if kw in lower_name:
                    return label
            return name  # raw name if no mapping match
    return None


def fill_hsmv_checkboxes(pdf_path: str, hsmv_data: dict) -> dict:
    """
    Fill weather and accident_type from AcroForm checkboxes.
    Only writes fields that are currently Unknown. Returns updated dict.
    """
    fields = extract_acroform_fields(pdf_path)
    if not fields:
        return hsmv_data

    result = dict(hsmv_data)

    if result.get("weather", "Unknown") == "Unknown":
        weather = _first_checked(fields, "weather", _WEATHER_KEYWORDS)
        if weather:
            result["weather"] = weather

    if result.get("accident_type", "Unknown") == "Unknown":
        accident = (
            _first_checked(fields, "crash_type", _ACCIDENT_KEYWORDS)
            or _first_checked(fields, "collision", _ACCIDENT_KEYWORDS)
            or _first_checked(fields, "manner", _ACCIDENT_KEYWORDS)
        )
        if accident:
            result["accident_type"] = accident

    return result
