"""
Post-extraction code decoder.

Translates raw numeric/alpha coded field values to human-readable strings
using the lookups/state_codes tables. Applied as a post-processing step
only for forms that use coded values (tx_cr3, fl_hsmv, ca_chp555, ny_mv104a,
pa_aa600).

Entry point: decode_record(record, form_id) → new dict
"""
from __future__ import annotations
import re
from lookups.state_codes import decode as _decode, tables_for_state
from core.form_classifier import state_from_form_id

# Fields to attempt code decoding on, per form_id.
# Only fields where we expect coded values are listed.
_DECODE_FIELDS: dict[str, list[str]] = {
    "tx_cr3":      ["weather", "light_condition", "accident_type", "road_surface", "contributing_factors", "injury_severity"],
    "fl_hsmv":     ["weather", "accident_type", "contributing_factors", "injury_severity"],
    "ca_chp555":   ["weather", "accident_type", "road_surface", "light_condition"],
    "ny_mv104a":   ["weather", "accident_type", "light_condition"],
    "pa_aa600":    ["weather", "accident_type", "road_surface", "light_condition"],
}

_MISSING = {"", "unknown", "n/a", "not found", "none"}


def decode_record(record: dict, form_id: str) -> dict:
    """
    Translate coded field values in an extracted record to human-readable strings.

    Only modifies fields that:
      1. Have a known coded-value table for this form_id
      2. Have a value that looks like a code (short numeric/alpha string)

    Returns a new dict; original record is not mutated.
    """
    fields_to_decode = _DECODE_FIELDS.get(form_id, [])
    if not fields_to_decode:
        return record

    state = state_from_form_id(form_id) or form_id
    result = dict(record)

    for field in fields_to_decode:
        raw = str(result.get(field) or "").strip()
        if not raw or raw.lower() in _MISSING:
            continue

        # Only attempt decode if value looks like a code:
        # - Pure numeric (e.g. "3", "01", "99")
        # - Single uppercase letter (e.g. "K", "A", "B" for TX injury)
        # - Comma/semicolon separated codes (e.g. "21, 22" TX contributing)
        # Skip values that are already long text (already decoded or from NER)
        if len(raw) > 30 and not re.match(r'^[\d,\s;/]+$', raw):
            continue

        decoded = _decode(state, field, raw)
        if decoded != raw:
            result[field] = decoded

    return result
