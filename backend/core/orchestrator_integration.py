import json
import os
import re
from core.document_model import Document
from core.template_schema import TemplateSchema, FieldDefinition, FieldStrategy
from core.orchestrator import extract
from database import get_custom_fields


def _normalize_compound_lines(text: str) -> str:
    """
    Police report compound lines pack multiple key-value pairs on one line without colons.
    This function replaces those lines with proper KEY: Value lines so every template's
    global_regex patterns can match them reliably.

    Examples handled:
      "Weather Rain Light Conditions Dark - Lighted Road Surface NWet"
        → "Weather: Rain\nLight Conditions: Dark - Lighted\nRoad Surface: Wet"

      "Road Alignment Curve & Grade Traffic Control No Controls Direction of Crash Same Direction (Chain Reaction)"
        → "Direction of Crash: Same Direction (Chain Reaction)"
    """
    out_lines = []

    for line in text.splitlines():
        clean = re.sub(r'\(cid:\d+\)', '', line).strip()

        # Compound weather/light/surface line
        m = re.match(
            r'(?i)^Weather\s+(?P<wx>.+?)\s+Light\s+Conditions\s+(?P<lc>.+?)\s+Road\s+Surface\s+N?(?P<rs>Dry|Wet|Snow|Ice|Slush|Sand|Mud|Oil|Water|Gravel|Other\S*)(?:\s|$)',
            clean
        )
        if m:
            out_lines.append(f"Weather: {m.group('wx').strip()}")
            lc = m.group('lc').strip()
            out_lines.append(f"Light Conditions: {lc}")
            out_lines.append(f"Light Condition: {lc}")   # alias used by most state templates
            out_lines.append(f"Road Surface: {m.group('rs').strip()}")
            continue

        # Partial weather line (no Road Surface match)
        m = re.match(r'(?i)^Weather\s+(?P<wx>.+?)\s+Light\s+Conditions\s+(?P<lc>.+)$', clean)
        if m:
            out_lines.append(f"Weather: {m.group('wx').strip()}")
            lc = m.group('lc').strip()
            out_lines.append(f"Light Conditions: {lc}")
            out_lines.append(f"Light Condition: {lc}")
            continue

        # Direction of Crash / manner of collision line — keep cleaned version and inject aliases
        # Pattern tolerates single-letter OCR artifact between "Direction" and "of" (e.g. "Direction Eof Crash")
        m = re.search(
            r'(?i)Direction\s+(?:[A-Z][ \t]*)?of\s+Crash\s+(?P<doc>.+?)(?:\s+Areas\s+of\s+Damage|$)',
            clean
        )
        if m:
            val = m.group('doc').strip()
            # Strip pdfplumber column-interleave uppercase artifacts from value
            val = re.sub(r'(?<=[a-z])[A-Z](?=[a-z])', '', val)   # ReEaction → Reaction
            val = re.sub(r'(?<=[a-z])[A-Z](?=\))', '', val)       # EndE) → End)
            val = re.sub(r'[A-Z]$', '', val).strip()               # trailing letter at string end
            # Keep a cleaned version of the original line (removes mid-word artifacts globally)
            cleaned_line = re.sub(r'(?<=[a-z])[A-Z](?=[a-z])', '', line)
            cleaned_line = re.sub(r'(?<=[a-z])[A-Z](?=\))', '', cleaned_line)
            out_lines.append(cleaned_line)
            # Inject aliases used by various state templates' accident_type patterns
            out_lines.append(f"Direction of Crash: {val}")
            out_lines.append(f"Manner of Collision: {val}")
            out_lines.append(f"Type of Crash: {val}")
            continue

        # Mid-line WEATHER label (sample file format: "CASE NUMBER xxx WEATHER Value")
        # Uppercase-only WEATHER avoids false positives in prose ("weather event", etc.)
        if not re.search(r'(?i)\bWeather\s*:', clean):
            m = re.search(
                r'\bWEATHER[ \t]+(?P<wx>.+?)(?=[ \t]+TYPE\s+OF\b|[ \t]+COLLISION\s+TYPE\b|\s*$)',
                clean
            )
            if m:
                wx = m.group('wx').strip()
                out_lines.append(line)
                out_lines.append(f"Weather: {wx}")
                continue

        # TYPE OF CollisionType / N (sample file format: "... TYPE OF value / 2")
        # Skips "TYPE OF COLLISION" which is a standard label handled by template patterns
        m = re.search(
            r'(?i)\bTYPE\s+OF\s+(?!COLLISION\b)(?P<val>.+?)(?=\s*/\s*\d|\s*$)',
            clean
        )
        if m:
            val = re.sub(r'\s*/\s*$', '', m.group('val').strip()).strip()
            if val:
                out_lines.append(line)
                out_lines.append(f"Direction of Crash: {val}")
                out_lines.append(f"Manner of Collision: {val}")
                out_lines.append(f"Type of Crash: {val}")
                continue

        # COLLISION TYPE Value (sample file format: "COLLISION TYPE value TOTAL VEHICLES N")
        m = re.search(
            r'(?i)\bCOLLISION\s+TYPE\s+(?P<val>.+?)(?=\s+TOTAL\s+(?:VEHICLES?|UNITS?)|\s*$)',
            clean
        )
        if m:
            val = m.group('val').strip()
            if val:
                out_lines.append(line)
                out_lines.append(f"Direction of Crash: {val}")
                out_lines.append(f"Manner of Collision: {val}")
                out_lines.append(f"Type of Crash: {val}")
                continue

        out_lines.append(line)

    return "\n".join(out_lines)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")

# form_id → template filename (state templates live in templates/)
_FORM_TEMPLATE_MAP: dict[str, str] = {
    # Original 5
    "ca_chp555":    "ca_chp555.json",
    "tx_cr3":       "tx_cr3.json",
    "ny_mv104a":    "ny_mv104a.json",
    "fl_hsmv":      "fl_hsmv90010.json",
    "pa_aa600":     "pa_aa600.json",
    # Tier 1 — High volume
    "oh_bmv2696":   "oh_bmv2696.json",
    "il_sr1":       "il_sr1.json",
    "ga_sr13":      "ga_sr13.json",
    "nc_dmv349":    "nc_dmv349.json",
    "nj_mv104":     "nj_mv104.json",
    "mi_ud10":      "mi_ud10.json",
    "va_fr300":     "va_fr300.json",
    "wa_422":       "wa_422.json",
    "az_40_8282":   "az_40_8282.json",
    "co_dr2447":    "co_dr2447.json",
    # Tier 2 — Medium volume
    "tn_cs0835":    "tn_cs0835.json",
    "in_sr13":      "in_sr13.json",
    "mo_1130":      "mo_1130.json",
    "wi_mv4002":    "wi_mv4002.json",
    "md_acrs":      "md_acrs.json",
    "mn_bca403":    "mn_bca403.json",
    "sc_sr309":     "sc_sr309.json",
    "al_acrs":      "al_acrs.json",
    "or_735":       "or_735.json",
    "ky_le35a":     "ky_le35a.json",
    "ok_sr22":      "ok_sr22.json",
    "ct_pr1":       "ct_pr1.json",
    "la_dotd390":   "la_dotd390.json",
    "ut_sr24":      "ut_sr24.json",
    "ms_cr2":       "ms_cr2.json",
    # Tier 3 — Lower volume
    "ar_crash":     "ar_crash.json",
    "ia_432015":    "ia_432015.json",
    "ks_trl1":      "ks_trl1.json",
    "ak_crash":     "ak_crash.json",
    "hi_hpd252":    "hi_hpd252.json",
    "id_itd3101":   "id_itd3101.json",
    "me_crash":     "me_crash.json",
    "ma_cra43":     "ma_cra43.json",
    "mt_crash":     "mt_crash.json",
    "ne_310c":      "ne_310c.json",
    "nh_dsmv311":   "nh_dsmv311.json",
    "nm_10516":     "nm_10516.json",
    "nd_sfn2086":   "nd_sfn2086.json",
    "ri_uc1":       "ri_uc1.json",
    "sd_crash":     "sd_crash.json",
    "vt_tsp300":    "vt_tsp300.json",
    "wv_crash":     "wv_crash.json",
    "wy_crash":     "wy_crash.json",
    "de_tc308":     "de_tc308.json",
    "dc_mpd":       "dc_mpd.json",
    "nv_nhp1":      "nv_nhp1.json",
}


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge_templates(base: dict, override: dict) -> dict:
    """
    Merge two template dicts. Override fields replace base fields with the
    same field_id; new override fields are appended.
    Returns a new dict — inputs are not mutated.
    """
    base_fields = {f["field_id"]: f for f in base.get("fields", [])}
    for field in override.get("fields", []):
        base_fields[field["field_id"]] = field  # replace or add
    merged = dict(base)
    merged["fields"] = list(base_fields.values())
    return merged


def run_orchestrator(
    canonical_doc: Document,
    doc_id: str,
    doc_type: str,
    form_id: str | None = None,
) -> dict:
    """
    Load the appropriate template (base + optional state-specific overlay),
    append dynamic custom fields, and run the extraction engine.

    Args:
        canonical_doc:  Parsed document.
        doc_id:         Document identifier (filename / DB key).
        doc_type:       Base template type: "police_report", "ia_report", etc.
        form_id:        Optional state form classifier result
                        (e.g. "tx_cr3", "ca_chp555"). When provided and a
                        matching state template exists, its fields are merged
                        on top of the base template.

    Returns:
        {record, review_flags, all_candidates}
    """
    # ── 1. Load base template ────────────────────────────────────────────────
    base_path = os.path.join(TEMPLATES_DIR, f"{doc_type}.json")
    if os.path.exists(base_path):
        template_data = _load_json(base_path)
    else:
        template_data = {
            "template_id": f"fallback_{doc_type}",
            "document_type": doc_type,
            "fields": [],
        }

    # ── 2. Overlay state-specific template if available ─────────────────────
    if form_id and form_id != "generic_mmucc":
        state_filename = _FORM_TEMPLATE_MAP.get(form_id)
        if state_filename:
            state_path = os.path.join(TEMPLATES_DIR, state_filename)
            if os.path.exists(state_path):
                state_data = _load_json(state_path)
                template_data = _merge_templates(template_data, state_data)

    # ── 3. Load into Pydantic model ──────────────────────────────────────────
    template = TemplateSchema(**template_data)

    # ── 4. Append custom fields (Human-in-the-Loop) ──────────────────────────
    custom_fields = get_custom_fields(doc_id)
    for field_name in custom_fields:
        patterns = [
            f"\\|[ \\t]*{re.escape(field_name)}[ \\t]*\\|[ \\t]*(?P<value>[^\\|\\n]+?)[ \\t]*\\|",
            f"(?im)^#+[ \\t]*{re.escape(field_name)}[^\\n]*\\n+(?P<value>.*?)(?:\\n#|\\n\\||$)",
            f"{re.escape(field_name)}[\\s:]+(?P<value>[^\\n]+)",
        ]
        dynamic_field = FieldDefinition(
            field_id=f"dynamic_{field_name}",
            display_name=field_name,
            field_type="text",
            strategies=[
                FieldStrategy(
                    strategy="global_regex",
                    priority=1,
                    config={
                        "patterns": patterns,
                        "flags": ["IGNORECASE", "DOTALL"],
                    },
                )
            ],
        )
        template.fields.append(dynamic_field)

    # ── 5. Normalize compound lines before extraction ───────────────────────
    canonical_doc.markdown = _normalize_compound_lines(canonical_doc.markdown or "")

    # ── 6. Run the engine ────────────────────────────────────────────────────
    result = extract(canonical_doc, template)

    review_flags = {
        entry["field_id"]: True
        for entry in result.get("audit", [])
        if entry.get("needs_review")
    }

    return {
        "record":         result["record"],
        "review_flags":   review_flags,
        "all_candidates": result.get("all_candidates", []),
    }
