import sys, os, pdfplumber, json
sys.path.insert(0, os.path.dirname(__file__))
from core.form_classifier import classify_form
from core.document_model import Document
from core.orchestrator_integration import run_orchestrator

sample_dir = r'C:\Users\ridea\Downloads\crash_reports_sample_set'

files = ['TX_Texas_high.pdf', 'TX_Texas_medium.pdf', 'CA_California_high.pdf',
         'FL_Florida_high.pdf', 'NY_New_York_high.pdf']

for fname in files:
    path = os.path.join(sample_dir, fname)
    parts = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages[:4]:
            parts.append(pg.extract_text() or '')
    text = '\n'.join(parts)

    form_id, conf = classify_form(text)
    doc = Document(document_id=fname, source_path=path, n_pages=2, markdown=text)
    result = run_orchestrator(doc, fname, 'police_report', form_id=form_id)
    record = result['record']

    print(f'=== {fname} (form={form_id}) ===')
    for k, v in record.items():
        if v in (None, '', [], 'null'):
            continue
        if isinstance(v, str) and v.startswith('['):
            try:
                items = json.loads(v)
                print(f'  {k}: [{len(items)} items]')
                for i, item in enumerate(items[:3]):
                    if 'name' in item:
                        print(f'    [{i}] name={item.get("name")} dob={item.get("dob")} addr={str(item.get("address",""))[:40]}')
                    else:
                        vin = item.get('vin', '?')
                        make = item.get('make', '?')
                        model = item.get('model', '?')
                        yr = item.get('year', '?')
                        ins = item.get('insurance_company', '?')
                        print(f'    [{i}] {yr} {make} {model} | VIN={vin} | ins={ins}')
            except Exception as e:
                print(f'  {k}: err={e}')
        elif isinstance(v, str) and len(v) > 100:
            print(f'  {k}: {v[:100]}...')
        else:
            print(f'  {k}: {v}')
    print('  NULL:', [k for k, v in record.items() if v in (None, '', [])])
    print()
