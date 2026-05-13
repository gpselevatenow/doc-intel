"""
Real confidence scoring for extracted records.
Replaces the hardcoded accuracy_score: 100.0 in all routes.
Returns (overall_0_100, per_field_scores_dict, reasons_list).
"""

import re

_WEIGHTS: dict[str, float] = {
    "date_time": 1.5,
    "location": 1.5,
    "report_number": 1.5,
    "agency": 1.2,
    "officer": 1.2,
    "cause_of_loss": 1.3,
    "inspection_date": 1.3,
    "inspection_firm": 1.2,
    "weather": 0.5,
    "accident_type": 0.7,
    "ems_agency": 0.7,
    "contributing_factors": 0.6,
    "property_damage": 0.5,
}

# Core fields are ALWAYS included in the denominator — missing them penalizes the score.
# Optional fields are only scored when there is evidence they appear in the document.
_CORE_FIELDS: dict[str, set] = {
    "police":    {"date_time", "location", "report_number", "agency", "officer", "weather", "accident_type"},
    "hsmv":      {"date_time", "location", "report_number", "agency", "officer", "weather", "accident_type"},
    "police_nv": {"date_time", "location", "report_number", "agency", "officer", "accident_type"},  # non-vehicle (no weather)
    "ia":        {"cause_of_loss", "inspection_date"},
}

# Incident types that indicate a non-traffic (no-weather) report
_NON_VEHICLE_INCIDENTS = re.compile(
    r'\b(?:larceny|theft|burglary|robbery|assault|vandalism|motor\s+vehicle\s+theft|'
    r'stolen\s+vehicle|hit\s+and\s+run\s+property|trespass|fraud|domestic)\b',
    re.IGNORECASE
)

_MISSING = {"", "unknown", "n/a", "not found", "none"}


def _field_score(field: str, val) -> tuple[float, str | None]:
    """Return (0.0–1.0 confidence, reason_if_low)."""
    if val is None or str(val).strip().lower() in _MISSING:
        return 0.0, f"{field}: not extracted"

    s = str(val).strip()

    if field in ("date_time", "inspection_date"):
        if re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', s):
            return 1.0, None
        if re.search(
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}',
            s, re.IGNORECASE
        ):
            return 1.0, None
        return 0.4, f"{field}: date format not recognized"

    if field == "report_number":
        if len(s.split()) > 4:
            return 0.2, f"{field}: looks like a sentence, not a case number"
        if re.match(r'^[\w\-/#]{3,25}$', s):
            return 1.0, None
        return 0.6, f"{field}: unusual format"

    if field == "subrogation":
        if s.lower() in ("yes", "no", "potential", "n/a", "none"):
            return 1.0, None
        return 0.7, None

    if field in ("coverage_a", "coverage_b", "coverage_c", "coverage_d", "settlement"):
        if re.search(r'\$[\d,]+', s):
            return 1.0, None
        if s.lower() in ("n/a", "not applicable", "excluded"):
            return 0.9, None
        return 0.5, f"{field}: no dollar amount found"

    if field == "location":
        if re.search(r'\d+\s+[A-Za-z]', s):
            return 1.0, None
        # Intersection or highway address (no street number, still valid)
        if re.search(r'&|\bI-\d+\b|\bUS-\d+\b|\bSR-\d+\b|\bMile Marker\b|\bExit\s+\d+', s, re.IGNORECASE):
            return 1.0, None
        if len(s) > 5:
            return 0.7, None
        return 0.3, f"{field}: location may be incomplete"

    return (1.0, None) if len(s) >= 3 else (0.5, f"{field}: value is very short")


def score_record(
    record: dict, doc_type: str = "police", all_candidates=None
) -> tuple[float, dict[str, int], list[str]]:
    """
    Score an extracted record by field coverage and value quality.

    When all_candidates is provided, only fields with extraction evidence
    (a candidate was found, or a non-empty value exists) are included in
    the denominator — fields absent from the document don't penalize the score.

    Returns (overall_0_100, per_field_pct_dict, reasons_list).
    """
    # Auto-detect non-vehicle incident types (larceny, theft, etc.) — no weather field
    if doc_type in ("police", "hsmv"):
        accident_type = str(record.get("accident_type") or "")
        if _NON_VEHICLE_INCIDENTS.search(accident_type):
            doc_type = "police_nv"

    if doc_type == "ia":
        scored = [
            "cause_of_loss", "inspection_date", "inspection_firm",
            "coverage_a", "coverage_b", "coverage_c", "coverage_d",
            "settlement", "subrogation",
        ]
    else:
        scored = [
            "date_time", "location", "report_number", "agency",
            "officer", "weather", "accident_type", "ems_agency",
            "contributing_factors", "property_damage",
        ]

    # Build set of fields with extraction evidence for presence-aware scoring
    fields_with_evidence: set[str] = set()
    if all_candidates is not None:
        for c in all_candidates:
            fid = c.field_id if hasattr(c, 'field_id') else (c.get('field_id') if isinstance(c, dict) else None)
            if fid:
                fields_with_evidence.add(fid)
    # Always include fields where a non-empty value was extracted (e.g. via NER)
    for fld in scored:
        val = record.get(fld)
        if val is not None and str(val).strip().lower() not in _MISSING:
            fields_with_evidence.add(fld)

    core_fields = _CORE_FIELDS.get(doc_type, set())

    per_field: dict[str, int] = {}
    reasons: list[str] = []
    weighted_sum = 0.0
    weight_total = 0.0

    for fld in scored:
        is_core = fld in core_fields
        # Core fields are always scored; optional fields only when evidence exists
        if not is_core and all_candidates is not None and fld not in fields_with_evidence:
            continue

        score, reason = _field_score(fld, record.get(fld))
        per_field[fld] = round(score * 100)
        w = _WEIGHTS.get(fld, 1.0)
        weighted_sum += score * w
        weight_total += w
        if reason:
            reasons.append(reason)

    if doc_type in ("police", "hsmv", "police_nv"):
        try:
            import json
            vehicles = record.get("vehicles")
            if isinstance(vehicles, str):
                vehicles = json.loads(vehicles or "[]")
            if vehicles:
                # Score vehicle record completeness (key fields per vehicle)
                key_veh_fields = ["vin", "plate", "make", "year", "model"]
                total_filled = sum(
                    1 for v in vehicles for f in key_veh_fields
                    if v.get(f) and str(v[f]).strip().lower() not in _MISSING
                )
                total_possible = len(vehicles) * len(key_veh_fields)
                completeness = total_filled / total_possible if total_possible else 0.0
                weighted_sum += completeness * 1.5
                weight_total += 1.5
            else:
                # No vehicles — only penalize traffic/crash reports, not theft/larceny
                is_traffic = doc_type in ("police", "hsmv")
                if is_traffic and any(
                    c.field_id if hasattr(c, 'field_id') else c.get('field_id', '') == 'vehicles'
                    for c in (all_candidates or [])
                ):
                    weighted_sum += 0.0
                    weight_total += 1.5
        except Exception:
            pass

    overall = round((weighted_sum / weight_total) * 100, 1) if weight_total else 0.0

    if not reasons:
        reasons = ["All key fields extracted successfully"]

    return overall, per_field, reasons
