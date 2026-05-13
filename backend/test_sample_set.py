"""
test_sample_set.py  --  run the classifier + extractor against the 70 PDFs
in the crash_reports_sample_set.

Usage:
    python test_sample_set.py [/path/to/crash_reports_sample_set]

Outputs:
  - Per-file: classified form_id, expected form_id, PASS/FAIL
  - Field fill-rate for each document
  - Summary table at the end
"""
import os, sys, textwrap
import pdfplumber

SAMPLE_DIR = (
    sys.argv[1]
    if len(sys.argv) > 1
    else r"C:\Users\ridea\Downloads\crash_reports_sample_set"
)

# ── Expected form_id per state, derived from the index README ────────────────
# Values must match keys in _FORM_TEMPLATE_MAP in orchestrator_integration.py
EXPECTED: dict[str, str] = {
    "CA": "ca_chp555",
    "TX": "tx_cr3",
    "FL": "fl_hsmv",
    "NY": "ny_mv104a",
    "PA": "pa_aa600",
    "IL": "il_sr1",
    "OH": "oh_bmv2696",
    "GA": "ga_sr13",
    "NC": "nc_dmv349",
    "MI": "mi_ud10",
    "NJ": "nj_mv104",
    "VA": "va_fr300",
    "WA": "wa_422",
    "AZ": "az_40_8282",
    "TN": "tn_cs0835",
    "MA": "ma_cra43",
    "IN": "in_sr13",
    "MO": "mo_1130",
    "MD": "md_acrs",
    "WI": "wi_mv4002",
    "CO": "co_dr2447",
    "MN": "mn_bca403",
    "SC": "sc_sr309",
    "AL": "al_acrs",
    "LA": "la_dotd390",
    "KY": "ky_le35a",
    "OR": "or_735",
    "OK": "ok_sr22",
    "CT": "ct_pr1",
    "UT": "ut_sr24",
    "IA": "ia_432015",
    "NV": "nv_nhp1",
    "AR": "ar_crash",
    "MS": "ms_cr2",
    "KS": "ks_trl1",
}

# ── Map state abbrev → PDF stems ─────────────────────────────────────────────
STATE_FILES: dict[str, list[str]] = {}
for fname in os.listdir(SAMPLE_DIR):
    if not fname.endswith(".pdf") or fname.startswith("00_"):
        continue
    abbrev = fname[:2]
    STATE_FILES.setdefault(abbrev, []).append(fname)

# ── Import pipeline ───────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from core.form_classifier import classify_form
from core.document_model import Document
from core.orchestrator_integration import run_orchestrator

def extract_text(path: str) -> str:
    """Fast pdfplumber text extraction — first 3 pages only (classifier only needs ~3000 chars)."""
    parts = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:3]:
                t = page.extract_text() or ""
                parts.append(t)
    except Exception as e:
        return f"[ERROR: {e}]"
    return "\n".join(parts)

def run_full(path: str, state: str, expected_form: str) -> dict:
    text = extract_text(path)
    form_id, conf = classify_form(text)

    # Build a minimal Document for extraction
    doc = Document(
        document_id=os.path.basename(path),
        source_path=path,
        n_pages=1,
        markdown=text,
    )

    try:
        result = run_orchestrator(doc, os.path.basename(path), "police_report", form_id=form_id)
        record = result["record"]
        filled = sum(1 for v in record.values() if v not in (None, "", []))
        total  = len(record)
        fill_pct = filled / total * 100 if total else 0
    except Exception as e:
        filled, total, fill_pct = 0, 0, 0
        record = {}

    return {
        "file":          os.path.basename(path),
        "state":         state,
        "expected":      expected_form,
        "got":           form_id,
        "conf":          conf,
        "classifier_ok": form_id == expected_form,
        "filled":        filled,
        "total":         total,
        "fill_pct":      fill_pct,
        "header_snippet": text[:200].replace("\n", " ").strip(),
    }


# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SAMPLE SET TEST -- classifier + extraction accuracy")
print("=" * 80)

results = []
missing_states = []

for state in sorted(EXPECTED.keys()):
    files = STATE_FILES.get(state, [])
    if not files:
        missing_states.append(state)
        continue
    for fname in sorted(files):
        path = os.path.join(SAMPLE_DIR, fname)
        r = run_full(path, state, EXPECTED[state])
        results.append(r)
        ok   = "[OK]  " if r["classifier_ok"] else "[FAIL]"
        tier = "high  " if "high" in fname else "med   "
        print(f"  {ok} {state} {tier} classify={r['got']:<20} fill={r['fill_pct']:5.1f}%")
        if not r["classifier_ok"]:
            print(f"         expected={r['expected']}")
            print(f"         header: {r['header_snippet'][:120]}")

# ─────────────────────────────────────────────────────────────────────────────
total_files     = len(results)
classify_pass   = sum(1 for r in results if r["classifier_ok"])
avg_fill        = sum(r["fill_pct"] for r in results) / total_files if total_files else 0
low_fill        = [r for r in results if r["fill_pct"] < 30]
classify_fail   = [r for r in results if not r["classifier_ok"]]

print()
print("=" * 80)
print(f"CLASSIFIER:  {classify_pass}/{total_files} correct ({classify_pass/total_files*100:.1f}%)")
print(f"AVG FILL:    {avg_fill:.1f}%")
if low_fill:
    print(f"LOW FILL (<30%): {len(low_fill)} files")
    for r in low_fill:
        print(f"  {r['file']:45s} {r['fill_pct']:.1f}%")
if missing_states:
    print(f"MISSING STATES (no PDF found): {missing_states}")
print()

# ── Classifier failures detail ────────────────────────────────────────────────
if classify_fail:
    print("CLASSIFIER FAILURES:")
    for r in classify_fail:
        print(f"  {r['file']}")
        print(f"    expected : {r['expected']}")
        print(f"    got      : {r['got']} (conf={r['conf']})")
        print(f"    header   : {r['header_snippet'][:160]}")
        print()

# ── Per-state fill summary ────────────────────────────────────────────────────
print("PER-STATE FILL RATE:")
state_fills: dict[str, list[float]] = {}
for r in results:
    state_fills.setdefault(r["state"], []).append(r["fill_pct"])
for st in sorted(state_fills):
    fills = state_fills[st]
    avg = sum(fills) / len(fills)
    bar = "#" * int(avg / 5)
    print(f"  {st}  {avg:5.1f}%  {bar}")

print("=" * 80)
