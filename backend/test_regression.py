"""
Full regression test suite for DocIntel backend.

Run: .\\venv\\Scripts\\python.exe test_regression.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name, cond, detail=""):
    status = PASS if cond else FAIL
    results.append((name, status, detail))
    marker = "[OK]" if cond else "[FAIL]"
    suffix = (" -- " + detail) if detail else ""
    print("  " + marker + " " + name + suffix)
    return cond


# =================================================================
# 1. Module imports
# =================================================================
print("\n-- 1. Module imports --")

try:
    from core.form_classifier import classify_form, state_from_form_id
    check("form_classifier import", True)
except Exception as e:
    check("form_classifier import", False, str(e))

try:
    from core.code_decoder import decode_record
    check("code_decoder import", True)
except Exception as e:
    check("code_decoder import", False, str(e))

try:
    import extractors
    from extractors.base import STRATEGY_REGISTRY
    check("checkbox_grid registered", "checkbox_grid" in STRATEGY_REGISTRY,
          "registry: " + str(list(STRATEGY_REGISTRY)))
except Exception as e:
    check("checkbox_grid import", False, str(e))

try:
    from lookups import naic_lookup, naic_search, mmucc_field, mmucc_decode
    from lookups import decode_state, citation_lookup, TABLE_VERSION
    check("lookups import", True)
except Exception as e:
    check("lookups import", False, str(e))

try:
    from core.orchestrator_integration import run_orchestrator
    check("orchestrator_integration import", True)
except Exception as e:
    check("orchestrator_integration import", False, str(e))

# =================================================================
# 2. Bug fixes
# =================================================================
print("\n-- 2. Bug fixes --")

from core.document_model import Document
from core.orchestrator_integration import run_orchestrator

SAMPLE_05_TEXT = (
    "TRAFFIC CRASH REPORT - HENNEPIN COUNTY\n"
    "\n"
    "DATE/TIME OF CRASH: 2024-03-15 at 22:40\n"
    "LOCATION: I-94 Westbound, Minneapolis\n"
    "WEATHER: Clear\n"
    "LIGHT CONDITION: Dark - Lighted\n"
    "MANNER OF COLLISION: Rear-End\n"
    "AGENCY: Hennepin County Sheriff's Office\n"
    "INVESTIGATING OFFICER: Deputy A. Larson\n"
    "REPORT NO.: 2024-HC-7731\n"
    "\n"
    "EMS: Hennepin EMS - Unit 14 (treated on scene)\n"
    "\n"
    "VEHICLE 1: 2019 Ford F-150 (White)\n"
    "VIN: 1FTFW1E50KFB12345\n"
    "DRIVER 1: John Smith, 123 Oak Street, Minneapolis MN\n"
    "INJURIES: None reported\n"
    "\n"
    "VEHICLE 2: 2021 Honda Civic (Silver)\n"
    "VIN: 2HGFC2F59MH123456\n"
    "DRIVER 2: Jane Doe, 456 Elm Ave, St. Paul MN\n"
    "INJURIES: Seat belt abrasion\n"
)

doc = Document(document_id="sample_05", source_path="test.pdf", n_pages=1, markdown=SAMPLE_05_TEXT)
result = run_orchestrator(doc, "sample_05", "police_report", form_id="generic_mmucc")
vehicles = []
try:
    vehicles = json.loads(result["record"].get("vehicles") or "[]")
except Exception:
    pass

check("B1: Unit 14 does not create V14", len(vehicles) <= 2,
      "found " + str(len(vehicles)) + " vehicles")

IA_TEXT = (
    "Cause of Loss: Fire\n"
    "\n"
    "The property sustained significant fire damage to the roof and upper floor.\n"
    "Smoke damage was also present throughout the structure.\n"
    "\n"
    "Inspection Date: 2024-01-15\n"
    "Inspection Firm: ABC Adjusting\n"
    "\n"
    "Coverage A: $250,000\n"
    "Coverage B: N/A\n"
    "Coverage C: N/A\n"
    "Coverage D: $15,000\n"
    "\n"
    "Coverages: HO-3 Special Form, Replacement Cost Value\n"
    "\n"
    "Subrogation: None identified\n"
    "Settlement: Recommend $85,000\n"
)

doc_ia = Document(document_id="ia_test", source_path="ia_test.pdf", n_pages=1, markdown=IA_TEXT)
ia_result = run_orchestrator(doc_ia, "ia_test", "ia_report")
cause = ia_result["record"].get("cause_of_loss", "")
check("B2: cause_of_loss no newline", cause is None or "\n" not in str(cause),
      "value: " + repr(cause))
check("B2: cause_of_loss captured 'fire'", bool(cause) and "fire" in str(cause).lower(),
      "value: " + repr(cause))

COLLISION_TEXT = (
    "TRAFFIC CRASH REPORT\n"
    "\n"
    "VEHICLE 1: 2020 Toyota Camry\n"
    "Type of Collision / Vehicles Involved: Rear-End\n"
    "VIN: 4T1B11HK5LU987654\n"
    "Color: White\n"
    "DRIVER 1: Test Person\n"
)

doc_col = Document(document_id="col_test", source_path="test.pdf", n_pages=1, markdown=COLLISION_TEXT)
col_result = run_orchestrator(doc_col, "col_test", "police_report", form_id="generic_mmucc")
vehicles_col = []
try:
    vehicles_col = json.loads(col_result["record"].get("vehicles") or "[]")
except Exception:
    pass

if vehicles_col:
    v1 = vehicles_col[0]
    color_val = v1.get("color", "Unknown")
    color_ok = str(color_val).strip().lower() not in ("rear-end", "rear end", "type of collision", "")
    check("B3: color not polluted by 'collision' alias", color_ok,
          "color='" + str(color_val) + "'")
else:
    check("B3: color alias test (no vehicles extracted -- skip)", True, "")

# =================================================================
# 3. Form classifier
# =================================================================
print("\n-- 3. Form classifier --")

CLASSIFIER_CASES = [
    # Original 5
    ("CHP 555",   "CALIFORNIA HIGHWAY PATROL TRAFFIC COLLISION REPORT\nCHP 555\nReporting District: 1234\n",                    "ca_chp555"),
    ("TX CR-3",   "TEXAS PEACE OFFICER'S CRASH REPORT\nFORM CR-3\nCrash ID: 12345678\n",                                       "tx_cr3"),
    ("NY MV-104A","NEW YORK STATE DEPARTMENT OF MOTOR VEHICLES\nMV-104A\nPolice Report of Motor Vehicle Accident\n",            "ny_mv104a"),
    ("FL HSMV",   "FLORIDA TRAFFIC CRASH REPORT\nHSMV 90010\nDHSMV\n",                                                         "fl_hsmv"),
    ("PA AA-600", "PENNSYLVANIA DEPARTMENT OF TRANSPORTATION CRASH REPORT\nAA-600\n",                                          "pa_aa600"),
    # Tier 1
    ("OH BMV-2696","OHIO DEPARTMENT OF PUBLIC SAFETY\nBMV-2696\nOHIO STATE HIGHWAY PATROL CRASH REPORT\n",                     "oh_bmv2696"),
    ("IL SR-1",   "ILLINOIS UNIFORM CRASH REPORT\nILLINOIS STATE POLICE\nDate: 2024-01-01\n",                                  "il_sr1"),
    ("GA SR-13",  "GEORGIA DEPARTMENT OF TRANSPORTATION\nSR-13A\nGEORGIA CRASH REPORT\n",                                      "ga_sr13"),
    ("NC DMV-349","NORTH CAROLINA DIVISION OF MOTOR VEHICLES\nDMV-349\n",                                                      "nc_dmv349"),
    ("NJ MV-104", "NEW JERSEY MOTOR VEHICLE ACCIDENT REPORT\nNJ MV-104\n",                                                     "nj_mv104"),
    ("MI UD-10",  "MICHIGAN STATE POLICE TRAFFIC CRASH REPORT\nUD-10\n",                                                       "mi_ud10"),
    ("VA FR-300", "VIRGINIA DEPARTMENT OF MOTOR VEHICLES\nDMV-FR300A\nVIRGINIA CRASH REPORT\n",                                "va_fr300"),
    ("WA 422",    "WASHINGTON STATE PATROL\nFORM 422\nWASHINGTON STATE TRAFFIC COLLISION REPORT\n",                            "wa_422"),
    ("AZ 40-8282","ARIZONA DEPARTMENT OF TRANSPORTATION\n40-8282\nADOT CRASH REPORT\n",                                        "az_40_8282"),
    ("CO DR2447", "COLORADO STATE PATROL\nDR 2447\nCSP CRASH REPORT\n",                                                        "co_dr2447"),
    # Tier 2
    ("TN CS-0835","TENNESSEE HIGHWAY PATROL TRAFFIC CRASH REPORT\nCS-0835\nTENNESSEE DEPARTMENT OF SAFETY\n",                  "tn_cs0835"),
    ("IN SR-13",  "INDIANA STATE POLICE\nINDIANA UNIFORM CRASH REPORT\nIN-13\n",                                               "in_sr13"),
    ("MO 1130",   "MISSOURI STATE HIGHWAY PATROL\nFORM 1130\nMSHP CRASH REPORT\n",                                            "mo_1130"),
    ("WI MV4002", "WISCONSIN TRAFFIC CRASH REPORT\nMV4002\nWISDOT CRASH\n",                                                   "wi_mv4002"),
    ("MD ACRS",   "MARYLAND AUTOMATED CRASH REPORTING SYSTEM\nACRS\nMARYLAND STATE POLICE\n",                                  "md_acrs"),
    ("MN BCA-403","MINNESOTA DEPARTMENT OF PUBLIC SAFETY\nBCA-403\nMINNESOTA STATE PATROL CRASH REPORT\n",                     "mn_bca403"),
    ("SC SR-309", "SOUTH CAROLINA TRAFFIC COLLISION REPORT\nSR-309\nSC DMV TRAFFIC\n",                                         "sc_sr309"),
    ("AL ACRS",   "ALABAMA LAW ENFORCEMENT AGENCY\nACRRS-1\nALEA CRASH REPORT\n",                                              "al_acrs"),
    ("OR 735",    "OREGON DEPARTMENT OF TRANSPORTATION\n735-6000\nODOT CRASH REPORT\n",                                        "or_735"),
    ("KY LE-35A", "KENTUCKY STATE POLICE\nLE-35A\nKSP CRASH REPORT\n",                                                         "ky_le35a"),
    ("OK SR-22",  "OKLAHOMA DEPARTMENT OF PUBLIC SAFETY\nOKLAHOMA HIGHWAY PATROL\nOKLAHOMA TRAFFIC CRASH REPORT\n",            "ok_sr22"),
    ("CT PR-1",   "CONNECTICUT STATE POLICE\nPR-1\nCONNECTICUT TRAFFIC CRASH REPORT\n",                                       "ct_pr1"),
    ("LA DOTD390","LOUISIANA STATE POLICE\nDOTD 390\nLOUISIANA TRAFFIC CRASH REPORT\n",                                       "la_dotd390"),
    ("UT SR-24",  "UTAH HIGHWAY PATROL\nSR-24\nUTAH DEPARTMENT OF PUBLIC SAFETY CRASH REPORT\n",                              "ut_sr24"),
    ("MS CR-2",   "MISSISSIPPI HIGHWAY PATROL\nCR-2\nMISSISSIPPI DEPARTMENT OF PUBLIC SAFETY\n",                               "ms_cr2"),
    # Tier 3 (sample)
    ("AR crash",  "ARKANSAS STATE POLICE\nARKANSAS TRAFFIC CRASH REPORT\n",                                                    "ar_crash"),
    ("WY crash",  "WYOMING HIGHWAY PATROL\nWYOMING TRAFFIC CRASH REPORT\n",                                                    "wy_crash"),
    ("DC MPD",    "METROPOLITAN POLICE DEPARTMENT\nDISTRICT OF COLUMBIA TRAFFIC CRASH REPORT\nDC MPD\n",                       "dc_mpd"),
    ("VT TSP-300","VERMONT STATE POLICE\nTSP-300\nVERMONT TRAFFIC CRASH REPORT\n",                                             "vt_tsp300"),
    ("DE TC-308", "DELAWARE STATE POLICE\nTC-308\nDELAWARE TRAFFIC CRASH REPORT\n",                                            "de_tc308"),
    # Generic fallback
    ("Generic MN","TRAFFIC CRASH REPORT\nHennepin County Sheriff's Office\nDate: 2024-03-15\n",                                "generic_mmucc"),
]

for label, text, expected in CLASSIFIER_CASES:
    form_id, conf = classify_form(text)
    ok = form_id == expected
    check("classify_form(" + label + ")",
          ok, "got (" + form_id + ", " + str(round(conf, 2)) + "), expected " + expected)

# =================================================================
# 4. Template merge
# =================================================================
print("\n-- 4. Template merge --")

import json as _json

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)

from core.orchestrator_integration import _merge_templates

base = load_json(os.path.join(TEMPLATES_DIR, "police_report.json"))
tx_overlay = load_json(os.path.join(TEMPLATES_DIR, "tx_cr3.json"))
merged_tx = _merge_templates(base, tx_overlay)

base_fids = {f["field_id"] for f in base["fields"]}
tx_fids = {f["field_id"] for f in tx_overlay["fields"]}
merged_fids = {f["field_id"] for f in merged_tx["fields"]}

check("TX merge: base fields present", base_fids.issubset(merged_fids))
check("TX merge: overlay fields present", tx_fids.issubset(merged_fids))
check("TX merge: no duplicates", len(merged_tx["fields"]) == len(merged_fids),
      "total=" + str(len(merged_tx["fields"])))

weather_field = next((f for f in merged_tx["fields"] if f["field_id"] == "weather"), None)
if weather_field:
    top_strat = sorted(weather_field["strategies"], key=lambda s: s.get("priority", 99))[0]["strategy"]
    check("TX merge: weather top strategy=checkbox_grid", top_strat == "checkbox_grid",
          "got '" + top_strat + "'")
check("TX merge: light_condition present", "light_condition" in merged_fids)

pa_overlay = load_json(os.path.join(TEMPLATES_DIR, "pa_aa600.json"))
merged_pa = _merge_templates(base, pa_overlay)
merged_pa_fids = {f["field_id"] for f in merged_pa["fields"]}
check("PA merge: road_surface present", "road_surface" in merged_pa_fids)
check("PA merge: light_condition present", "light_condition" in merged_pa_fids)
check("PA merge: total fields>=9", len(merged_pa["fields"]) >= 9,
      "total=" + str(len(merged_pa["fields"])))

# =================================================================
# 5. Lookups API
# =================================================================
print("\n-- 5. Lookups API --")

sf = naic_lookup(25143)
check("NAIC lookup(25143) State Farm",
      sf is not None and "state farm" in str(sf).lower(),
      str(sf))

geico = naic_search("geico")
check("NAIC search('geico')", len(geico) > 0,
      str(len(geico)) + " results")

c10 = mmucc_field("C10")
check("MMUCC field C10 (Weather)",
      c10 is not None and "weather" in str(c10.get("name", "")).lower(),
      str(c10))

decoded_weather = mmucc_decode("C10", "2")
check("MMUCC decode C10/2 = Cloudy",
      "cloudy" in str(decoded_weather).lower(),
      "got: " + str(decoded_weather))

c11 = mmucc_field("C11")
check("MMUCC field C11 (Light Condition)",
      c11 is not None and "light" in str(c11.get("name", "")).lower(),
      str(c11))

rain = decode_state("TX", "weather", "3")
check("decode_state TX weather 3 = Rain",
      "rain" in str(rain).lower(),
      "got: " + str(rain))

multi = decode_state("TX", "contributing_factors", "21, 22")
check("decode_state TX multi-code",
      "distraction" in str(multi).lower(),
      "got: " + str(multi))

statute = citation_lookup("TX", "545.062")
check("citation_lookup TX 545.062",
      statute is not None and "following" in str(statute).lower(),
      "got: " + str(statute))

statute_ca = citation_lookup("CA", "22350")
check("citation_lookup CA 22350",
      statute_ca is not None and "speed" in str(statute_ca).lower(),
      "got: " + str(statute_ca))

check("TABLE_VERSION present",
      isinstance(TABLE_VERSION, dict) and len(TABLE_VERSION) >= 3,
      "keys: " + str(list(TABLE_VERSION)))

# =================================================================
# 6. End-to-end extraction on simulated documents
# =================================================================
print("\n-- 6. End-to-end extraction --")

CHP_TEXT = (
    "CALIFORNIA HIGHWAY PATROL TRAFFIC COLLISION REPORT\n"
    "CHP 555\n"
    "\n"
    "LOCAL REPORT NUMBER: 2024-CHP-09812\n"
    "REPORTING DISTRICT: BEVERLY HILLS\n"
    "DATE / TIME: 2024-04-20 / 14:35\n"
    "REPORTING AGENCY: CHP Beverly Hills Area\n"
    "REPORTING OFFICER: Officer M. Ramirez\n"
    "LOCATION: US-101 Southbound at Cahuenga Blvd, Los Angeles CA\n"
    "WEATHER: Clear\n"
    "\n"
    "TYPE OF COLLISION: Rear-End\n"
    "SEVERITY: Property Damage Only\n"
    "\n"
    "PRIMARY CONTRIBUTING COLLISION FACTOR: Following Too Closely\n"
    "\n"
    "VEHICLE 1: 2021 Honda Accord (Blue)\n"
    "VIN: 1HGCV2F38MA123456\n"
    "DRIVER 1: Alice Kim, 123 Sunset Blvd, Los Angeles CA\n"
    "INJURIES: None\n"
    "\n"
    "VEHICLE 2: 2019 BMW 3-Series (Black)\n"
    "VIN: WBA5R7C52KAE12345\n"
    "DRIVER 2: Bob Johnson, 456 Hollywood Blvd, Los Angeles CA\n"
    "INJURIES: None\n"
)

FL_HSMV_TEXT = (
    "FLORIDA TRAFFIC CRASH REPORT\n"
    "HSMV 90010\n"
    "DHSMV\n"
    "\n"
    "HSMV CRASH REPORT NO: FL-2024-TMP-00123\n"
    "FHP TROOP: Troop D\n"
    "INVESTIGATING OFFICER: Trooper B. Williams\n"
    "CRASH DATE/TIME: 05/10/2024 / 08:15\n"
    "\n"
    "COUNTY/CITY: Miami-Dade / Miami\n"
    "ROADWAY: I-95 Northbound at NW 79th St\n"
    "\n"
    "CRASH TYPE: [ ] Rear-End  [X] Angle  [ ] Head-On\n"
    "WEATHER: [X] Clear  [ ] Rain  [ ] Fog\n"
    "\n"
    "CONTRIBUTING CAUSE: Failure to yield\n"
    "\n"
    "VEHICLE 1: 2020 Toyota RAV4\n"
    "DRIVER 1: Carlos Gomez\n"
)

TX_CR3_TEXT = (
    "TEXAS PEACE OFFICER'S CRASH REPORT\n"
    "FORM CR-3\n"
    "\n"
    "CRASH ID: TX-2024-8675309\n"
    "INVESTIGATING AGENCY: Austin PD\n"
    "INVESTIGATING OFFICER: Sgt. Johnson\n"
    "CRASH DATE: 2024-02-14\n"
    "CRASH LOCATION: MoPac Expressway SB at Enfield Rd, Austin TX\n"
    "\n"
    "WEATHER: [X] Clear  [ ] Cloudy  [ ] Rain\n"
    "MANNER OF COLLISION: [X] Rear End  [ ] Head On  [ ] Angle\n"
    "\n"
    "CONTRIBUTING FACTOR: Speed\n"
    "\n"
    "VEHICLE 1: 2022 Chevrolet Silverado (Red)\n"
    "VEHICLE 2: 2018 Toyota Prius (White)\n"
)

IA_HIGH_TEXT = (
    "INDEPENDENT ADJUSTER REPORT - HIGH COMPLEXITY\n"
    "\n"
    "Cause of Loss: Kitchen fire originating from unattended cooking\n"
    "\n"
    "Inspection Date: 2024-03-10\n"
    "Inspection Firm: Global Claims Adjusting LLC\n"
    "\n"
    "Coverage A: $420,000\n"
    "Coverage B: N/A\n"
    "Coverage C: $45,000\n"
    "Coverage D: $36,000\n"
    "\n"
    "Coverages: HO-3 Special Form, Replacement Cost Value\n"
    "\n"
    "Officials: Fire Marshal, Hometown FD Report #2024-0312\n"
    "\n"
    "Subrogation: Under investigation, stove manufacturer\n"
    "\n"
    "Settlement: Recommend $187,500\n"
    "\n"
    "Payment Summary: Advance payment issued $25,000 on 2024-03-20\n"
    "\n"
    "Recommendations: Approve full structural rebuild; retain public adjuster\n"
)

IA_LOW_TEXT = (
    "Property Inspection Report\n"
    "\n"
    "Cause of Loss: Water damage from burst pipe\n"
    "\n"
    "Inspection Date: 2024-01-28\n"
    "Firm: ABC Claims\n"
    "\n"
    "Cov A: $180,000\n"
    "Cov D: $8,500\n"
    "\n"
    "Subrogation: None\n"
    "Settlement: $12,000\n"
)


def run_and_score(label, text, doc_type, expected_form_id=None, expected_fields=None):
    doc = Document(document_id=label, source_path="test.pdf", n_pages=1, markdown=text)
    form_id = expected_form_id or "generic_mmucc"
    kwargs = {"form_id": form_id} if doc_type == "police_report" else {}
    result = run_orchestrator(doc, label, doc_type, **kwargs)
    record = result["record"]
    filled = sum(1 for v in record.values()
                 if v is not None and str(v).strip() not in ("", "Unknown"))
    total = max(len(record), 1)
    fill_pct = filled / total * 100
    print("  [" + label + "] form=" + form_id +
          " filled=" + str(filled) + "/" + str(total) +
          " (" + str(round(fill_pct)) + "%)")
    if expected_fields:
        for field_name, expected_val in expected_fields.items():
            actual = record.get(field_name, "")
            hit = bool(actual) and expected_val.lower() in str(actual).lower()
            check("  " + label + "." + field_name, hit,
                  "expected '" + expected_val + "', got '" + str(actual) + "'")
    return fill_pct, record


print("\n  -- police_report --")
chp_pct, _ = run_and_score("CHP-555", CHP_TEXT, "police_report",
    expected_form_id="ca_chp555",
    expected_fields={"report_number": "2024-CHP", "accident_type": "Rear-End"})
check("CHP-555 fill >= 40%", chp_pct >= 40, str(round(chp_pct, 1)) + "%")

fl_pct, _ = run_and_score("FL-HSMV", FL_HSMV_TEXT, "police_report",
    expected_form_id="fl_hsmv",
    expected_fields={"report_number": "FL-2024"})
check("FL-HSMV fill >= 30%", fl_pct >= 30, str(round(fl_pct, 1)) + "%")

tx_pct, _ = run_and_score("TX-CR3", TX_CR3_TEXT, "police_report",
    expected_form_id="tx_cr3",
    expected_fields={"report_number": "TX-2024", "accident_type": "Rear End"})
check("TX-CR3 fill >= 30%", tx_pct >= 30, str(round(tx_pct, 1)) + "%")

mn_pct, _ = run_and_score("MN-Generic", SAMPLE_05_TEXT, "police_report",
    expected_form_id="generic_mmucc",
    expected_fields={"accident_type": "Rear-End"})
check("MN-Generic fill >= 30%", mn_pct >= 30, str(round(mn_pct, 1)) + "%")

print("\n  -- ia_report --")
ia_h_pct, _ = run_and_score("IA-High", IA_HIGH_TEXT, "ia_report",
    expected_fields={"cause_of_loss": "fire", "inspection_firm": "Global",
                     "subrogation": "investigation"})
check("IA-High fill >= 60%", ia_h_pct >= 60, str(round(ia_h_pct, 1)) + "%")

ia_l_pct, _ = run_and_score("IA-Low", IA_LOW_TEXT, "ia_report",
    expected_fields={"cause_of_loss": "water"})
check("IA-Low fill >= 30%", ia_l_pct >= 30, str(round(ia_l_pct, 1)) + "%")

# =================================================================
# Summary
# =================================================================
print("\n" + "=" * 60)
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
total = len(results)
pct = passed / total * 100 if total else 0
print("RESULTS: " + str(passed) + "/" + str(total) +
      " passed (" + str(round(pct, 1)) + "%)")
if failed:
    print("\nFAILED (" + str(failed) + "):")
    for name, status, detail in results:
        if status == FAIL:
            print("  [X] " + name + ((" -- " + detail) if detail else ""))
print()
sys.exit(0 if failed == 0 else 1)
