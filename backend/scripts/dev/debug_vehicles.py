import sys, os, json, pdfplumber
sys.path.insert(0, os.path.dirname(__file__))
from core.document_model import Document
from core.form_classifier import classify_form
from core.orchestrator_integration import run_orchestrator

base = r"C:\Users\ridea\OneDrive\Desktop\VS Projects\doc-intel\sample documents"
for fname in ["sample_full_report.pdf", "sample_21_fog_5veh_houston.pdf", "Police_Report_High_Complexity.pdf"]:
    path = os.path.join(base, fname)
    parts = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            parts.append(pg.extract_text() or "")
    text = "\n".join(parts)
    form_id, conf = classify_form(text)
    doc = Document(document_id=fname, source_path=path, n_pages=2, markdown=text)
    result = run_orchestrator(doc, fname, "police_report", form_id=form_id)
    record = result["record"]
    v = record.get("vehicles")
    p = record.get("parties")
    v_list = json.loads(v) if v else []
    p_list = json.loads(p) if p else []
    print(f"{fname}: vehicles={len(v_list)} parties={len(p_list)}")
    for i, veh in enumerate(v_list):
        yr = veh.get("year"); mk = veh.get("make"); mo = veh.get("model")
        vin = veh.get("vin"); pl = veh.get("plate"); ins = (veh.get("insurance_company") or "")[:30]
        print(f"  V{i+1}: {yr} {mk} {mo} | VIN={vin} plate={pl} ins={ins}")
    for i, pt in enumerate(p_list):
        role = pt.get("role"); name = pt.get("name"); dob = pt.get("dob")
        addr = (pt.get("address") or "")[:40]
        print(f"  P{i+1}: role={role} name={name} dob={dob} addr={addr}")
    print()
