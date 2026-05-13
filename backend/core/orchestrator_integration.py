import json
import os
import re
from core.document_model import Document
from core.template_schema import TemplateSchema, FieldDefinition, FieldStrategy
from core.orchestrator import extract
from database import get_custom_fields

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

    # ── 5. Run the engine ────────────────────────────────────────────────────
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
