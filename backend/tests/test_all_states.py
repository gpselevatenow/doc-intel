"""Quick vehicle/party/witness extraction sweep across the full sample set."""
import sys, os, pdfplumber, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.form_classifier import classify_form
from core.document_model import Document
from core.orchestrator_integration import run_orchestrator

sample_dir = r'C:\Users\ridea\Downloads\crash_reports_sample_set'

files = sorted(f for f in os.listdir(sample_dir) if f.endswith('.pdf'))

total = ok_v = ok_p = ok_w = 0
failures = []

for fname in files:
    path = os.path.join(sample_dir, fname)
    parts = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages[:4]:
            parts.append(pg.extract_text() or '')
    text = '\n'.join(parts)

    form_id, _ = classify_form(text)
    doc = Document(document_id=fname, source_path=path, n_pages=len(parts), markdown=text)
    result = run_orchestrator(doc, fname, 'police_report', form_id=form_id)
    record = result['record']

    def parse_list(key):
        try:
            return json.loads(record.get(key) or '[]')
        except Exception:
            return []

    v = parse_list('vehicles')
    p = parse_list('parties')
    w = parse_list('witnesses')
    complexity = 'high' if '_high' in fname else 'medium'
    expected_v = 3 if complexity == 'high' else 2
    expected_p = 3 if complexity == 'high' else 2

    v_ok = len(v) >= expected_v
    p_ok = len(p) >= expected_p
    w_ok = len(w) >= 1 if complexity == 'high' else True

    total += 1
    if v_ok: ok_v += 1
    if p_ok: ok_p += 1
    if w_ok: ok_w += 1

    status = 'OK' if (v_ok and p_ok) else 'XX'
    if not (v_ok and p_ok):
        failures.append(fname)
    print(f"{status} {fname:<40} form={form_id:<16} V={len(v)}/{expected_v} P={len(p)}/{expected_p} W={len(w)}")

print()
print(f"{'='*70}")
print(f"TOTAL: {total} files")
print(f"Vehicles ≥ expected:  {ok_v}/{total} ({100*ok_v//total}%)")
print(f"Parties ≥ expected:   {ok_p}/{total} ({100*ok_p//total}%)")
print(f"Witnesses ≥ 1 (high): {ok_w}/{total}")
if failures:
    print(f"\nFailed ({len(failures)}):")
    for f in failures:
        print(f"  {f}")
