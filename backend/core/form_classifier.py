"""
State police report form classifier.

Stage 1: Deterministic fingerprint matching — covers ~95% of known forms.
         Looks for form numbers and agency names in the document header.
Stage 2: Returns "generic_mmucc" when no fingerprint matches.

Returns (form_id, confidence) where:
  form_id     str  — one of the known state form_ids or generic_mmucc
  confidence  float — 0.95 for fingerprint match, 0.4 for fallback

Design rule: every state entry must include BOTH a form-number pattern AND a
             standalone agency/title pattern so either alone is sufficient.
             Proximity patterns (.{0,N}) must never be the only option — they
             fail when pdfplumber reflows multi-column headers.
"""
from __future__ import annotations
import re

# (form_id, patterns) — first pattern that matches determines the form.
# Ordered most-specific first to prevent false positives.
_FINGERPRINTS: list[tuple[str, list[str]]] = [

    # ── CA ────────────────────────────────────────────────────────────────────
    ("ca_chp555", [
        r'CHP[\s\-]*555\b',
        r'OTS\s+(?:FORM\s+)?555',
        r'CALIFORNIA\s+HIGHWAY\s+PATROL.{0,80}(?:COLLISION|CRASH)\s+REPORT',
        r'(?:REPORTING\s+DISTRICT|BEAT\s+NUMBER).{0,40}CHP',
    ]),

    # ── TX ────────────────────────────────────────────────────────────────────
    ("tx_cr3", [
        r'\bFORM\s+CR[-\s]*3\b',
        r'\bCR[-–]3\b.{0,40}(?:TEXAS|CRASH)',
        r'TEXAS\s+PEACE\s+OFFICER',
        r'TXDOT.{0,40}CRASH\s+REPORT',
        r'TEXAS\s+DEPARTMENT\s+OF\s+TRANSPORTATION.{0,40}CRASH',
        # TX city-agency collision reports (FWPD, HPD — not CR-3 forms but TX-jurisdiction docs)
        r'Fort\s+Worth\s+Police\s+Department',
        r'Houston\s+Police\s+Department',
        r'\bTxDPS\b',
        r'\bTxDOT\b',
        r'\bFWPD-\d{2}-\d{2}',
        r'\bHPD-\d{2}-\d{2}-\d{2}',
    ]),

    # ── Municipal city PD collision reports ──────────────────────────────────
    # These are internal city-agency forms, not state-standardized crash forms.
    # Positioned before state fingerprints to prevent il_sr1 / state false-positives.
    # Template resolution: intentionally absent from _FORM_TEMPLATE_MAP in
    # orchestrator_integration.py → falls through to police_report.json base
    # template (same behavior as generic_mmucc).
    ("municipal_pd_collision", [
        r'Los\s+Angeles\s+Police\s+Department',
        r'New\s+York\s+City\s+Police\s+Department',
        r'Philadelphia\s+Police\s+Department',
        r'Tampa\s+Police\s+Department',
        r'\bLAPD-\d{2}-\d{2}-\d{2}-\d{2,4}\b',
        r'\bNYPD-\d{2}-\d{2}-\d{2}-\d{2,4}\b',
        r'\bPPD-\d{2}-\d{2}-\d{2}-\d{2,4}\b',
        r'\bTPD-\d{2}-\d{2}-\d{2}-\d{2,4}\b',
    ]),

    # ── NY — must require the A to avoid matching NJ NJTR-1 ──────────────────
    ("ny_mv104a", [
        r'\bMV[-\s]*104[-\s]*A\b',
        r'NEW\s+YORK\s+STATE\s+DEPARTMENT\s+OF\s+MOTOR\s+VEHICLES',
        r'POLICE\s+REPORT\s+OF\s+MOTOR\s+VEHICLE\s+ACCIDENT',
        r'NEW\s+YORK\s+(?:DMV|MVR)',
    ]),

    # ── FL ────────────────────────────────────────────────────────────────────
    ("fl_hsmv", [
        r'HSMV\s*9001',
        r'FLORIDA\s+TRAFFIC\s+CRASH\s+REPORT',
        r'FLORIDA\s+DEPARTMENT\s+OF\s+HIGHWAY\s+SAFETY\s+AND\s+MOTOR\s+VEHICLES',
        r'\bFHSMV\b',
        r'\bDHSMV\b',
    ]),

    # ── PA — AA-500 (current) and AA-600 (prior revision) ────────────────────
    ("pa_aa600", [
        r'\bAA[-\s]*[56]00\b',
        r'POLICE\s+CRASH\s+REPORTING\s+FORM',
        r'PENNSYLVANIA\s+STATE\s+POLICE.{0,60}CRASH',
        r'COMMONWEALTH\s+OF\s+PENNSYLVANIA.{0,80}CRASH\s+REPORT',
        r'PennDOT.{0,60}(?:CRASH|ACCIDENT)',
    ]),

    # ── OH — OH-1 (current) and BMV-2696 (prior) ─────────────────────────────
    ("oh_bmv2696", [
        r'\bBMV[-\s]*2696\b',
        r'\bOH[-\s]*1\b.{0,40}(?:OHIO|OSHP|PATROL)',
        r'OHIO\s+TRAFFIC\s+CRASH\s+REPORT',
        r'OHIO\s+STATE\s+HIGHWAY\s+PATROL\b',
        r'\bOSHP\b',
    ]),

    # ── IL — SR-1050 (current) and SR-1 (prior) ──────────────────────────────
    ("il_sr1", [
        r'\bSR[-\s]*1050\b',
        r'\bILLINOIS\s+UNIFORM\s+CRASH\s+REPORT\b',
        r'\bSR[-\s]*1\b.{0,40}(?:ILLINOIS|IDOT|ISP)',
        r'ILLINOIS\s+TRAFFIC\s+CRASH\s+REPORT',
        r'ILLINOIS\s+DEPARTMENT\s+OF\s+TRANSPORTATION\b',
    ]),

    # ── GA — DPS-523 (current) and SR-13 (prior) ─────────────────────────────
    ("ga_sr13", [
        r'\bDPS[-\s]*523\b',
        r'\bSR[-\s]*13[A]?\b.{0,40}GEORGIA',
        r'UNIFORM\s+MOTOR\s+VEHICLE\s+ACCIDENT.{0,40}GEORGIA',
        r'GEORGIA\s+CRASH\s+REPORT',
        r'GEORGIA\s+DEPARTMENT\s+OF\s+(?:PUBLIC\s+SAFETY|TRANSPORTATION)\b',
    ]),

    # ── NC ────────────────────────────────────────────────────────────────────
    ("nc_dmv349", [
        r'\bDMV[-\s]*349\b',
        r'NORTH\s+CAROLINA\s+CRASH\s+REPORT',
        r'NORTH\s+CAROLINA\s+(?:DIVISION\s+OF\s+MOTOR\s+VEHICLES|DMV).{0,60}CRASH',
        r'NORTH\s+CAROLINA\s+STATE\s+HIGHWAY\s+PATROL\b',
        r'\bNCDMV\b',
    ]),

    # ── NJ — NJTR-1 (current) and MV-104 (prior) — must come before NY ───────
    ("nj_mv104", [
        r'\bNJTR[-\s]*1\b',
        r'\bNJ\s+MV[-\s]*104\b',
        r'\bNEW\s+JERSEY\s+MV[-\s]*104\b',
        r'POLICE\s+CRASH\s+INVESTIGATION.{0,40}NEW\s+JERSEY',
        r'NEW\s+JERSEY\s+(?:DIVISION\s+OF\s+STATE\s+POLICE|MOTOR\s+VEHICLE\s+COMMISSION)\b',
        r'\bNJMVC\b',
    ]),

    # ── MI ────────────────────────────────────────────────────────────────────
    ("mi_ud10", [
        r'\bUD[-\s]*10\b',
        r'MICHIGAN\s+TRAFFIC\s+CRASH\s+REPORT',
        r'MICHIGAN\s+STATE\s+POLICE\b',
    ]),

    # ── VA — FR-300P (current) ────────────────────────────────────────────────
    ("va_fr300", [
        r'\bFR[-\s]*300[PA]?\b',
        r'VIRGINIA\s+(?:POLICE\s+)?CRASH\s+REPORT',
        r'VIRGINIA\s+STATE\s+POLICE\b',
        r'VIRGINIA\s+DEPARTMENT\s+OF\s+MOTOR\s+VEHICLES\b',
        r'\bVSP\b.{0,40}FR[-\s]*300',
    ]),

    # ── WA — PTCR (current) and Form-422 (prior) ─────────────────────────────
    ("wa_422", [
        r'\bPTCR\b',
        r'\bWSP\s+FORM\s+422\b',
        r'\bFORM\s+422\b.{0,40}(?:WSP|WASHINGTON)',
        r'POLICE\s+TRAFFIC\s+COLLISION\s+REPORT',
        r'WASHINGTON\s+STATE\s+PATROL\b',
    ]),

    # ── AZ — AZ-DPS-CR (current) and 40-8282 (prior) ─────────────────────────
    ("az_40_8282", [
        r'\bAZ[-\s]*DPS[-\s]*CR\b',
        r'\b40[-\s]*8282\b',
        r'ARIZONA\s+CRASH\s+REPORT',
        r'ARIZONA\s+DEPARTMENT\s+OF\s+PUBLIC\s+SAFETY\b',
    ]),

    # ── CO — DR-3447 (current) and DR-2447 (prior) ───────────────────────────
    ("co_dr2447", [
        r'\bDR[-\s]*[23]447\b',
        r'COLORADO\s+TRAFFIC\s+CRASH\s+REPORT',
        r'COLORADO\s+STATE\s+PATROL\b',
    ]),

    # ── TN — THP-86 (current) and CS-0835 (prior) ────────────────────────────
    ("tn_cs0835", [
        r'\bTHP[-\s]*86\b',
        r'\bCS[-\s]*0835\b',
        r'TENNESSEE\s+UNIFORM\s+CRASH\s+REPORT',
        r'TENNESSEE\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── IN — ARIES OSCR (current) and IN-13 (prior) ──────────────────────────
    ("in_sr13", [
        r'\bARIES\s+OSCR\b',
        r'\bIN[-\s]*13\b',
        r"OFFICER'S\s+STANDARD\s+CRASH.{0,40}INDIANA",
        r'INDIANA\s+(?:UNIFORM\s+)?CRASH\s+REPORT',
        r'INDIANA\s+STATE\s+POLICE\b',
    ]),

    # ── MO — MoDOT STARS (current) and Form-1130 (prior) ─────────────────────
    ("mo_1130", [
        r'MoDOT\s+STARS',
        r'\bFORM\s+1130\b',
        r'\bMSHP\s+(?:FORM\s+)?1130\b',
        r'MISSOURI\s+UNIFORM\s+CRASH\s+REPORT',
        r'MISSOURI\s+STATE\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── WI — DT4000 (current) and MV-4002 (prior) ────────────────────────────
    ("wi_mv4002", [
        r'\bDT[-\s]*4000\b',
        r'\bMV[-\s]*4002\b',
        r'WISCONSIN\s+MOTOR\s+VEHICLE\s+CRASH\s+REPORT',
        r'WISCONSIN\s+DEPARTMENT\s+OF\s+TRANSPORTATION\b',
    ]),

    # ── MD — ACRS form name appears before "MARYLAND" in reflow ──────────────
    ("md_acrs", [
        r'AUTOMATED\s+CRASH\s+REPORTING\s+SYSTEM',
        r'\bACRS\b.{0,60}(?:MARYLAND|MSP)',
        r'MARYLAND\s+STATE\s+POLICE\b',
    ]),

    # ── MN — PR1/MNCrash (current) and BCA-403 (prior) ───────────────────────
    ("mn_bca403", [
        r'\bMNCrash\b',
        r'\bPR[-\s]*1\b.{0,40}(?:MINNESOTA|MNCRASH)',
        r'\bBCA[-\s]*403\b',
        r'MINNESOTA\s+PEACE\s+OFFICER',
        r'MINNESOTA\s+STATE\s+PATROL\b',
    ]),

    # ── SC — TR-310 (current) and SR-309 (prior) ─────────────────────────────
    ("sc_sr309", [
        r'\bTR[-\s]*310\b',
        r'\bSR[-\s]*309\b',
        r'SC\s+TRAFFIC\s+COLLISION\s+REPORT',
        r'SOUTH\s+CAROLINA\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── AL — eCrash (current) and ACRRS/ACRS (prior) ─────────────────────────
    ("al_acrs", [
        r'\beCrash\b',
        r'\bACRRS\b',
        r'ALABAMA\s+LAW\s+ENFORCEMENT\b',
        r'UNIFORM\s+TRAFFIC\s+CRASH\s+REPORT.{0,40}ALABAMA',
    ]),

    # ── OR — DMV 735-32 (current) and 735-6000 (prior) ───────────────────────
    ("or_735", [
        r'\bDMV[-\s]*735[-\s]*3[26]\b',
        r'\b735[-\s]*6000[A]?\b',
        r'OREGON\s+POLICE\s+TRAFFIC\s+CRASH\s+REPORT',
        r'OREGON\s+STATE\s+POLICE\b.{0,40}(?:CRASH|REPORT)',
    ]),

    # ── KY — KYOPS/CRT-1 (current) and LE-35A (prior) ────────────────────────
    ("ky_le35a", [
        r'\bKYOPS\b',
        r'\bCRT[-\s]*1\b.{0,40}(?:KENTUCKY|KSP)',
        r'\bLE[-\s]*35[A]?\b',
        r'KENTUCKY\s+UNIFORM\s+POLICE\s+TRAFFIC\s+COLLISION',
        r'KENTUCKY\s+STATE\s+POLICE\b',
    ]),

    # ── OK — OCR (current) and SR-22 (prior) ─────────────────────────────────
    ("ok_sr22", [
        r'\bOCR\b.{0,40}OKLAHOMA',
        r'OKLAHOMA\s+OFFICIAL\s+TRAFFIC\s+COLLISION\s+REPORT',
        r'\bOK(?:LAHOMA)?\s+SR[-\s]*22\b',
        r'OKLAHOMA\s+(?:TRAFFIC\s+)?CRASH\s+REPORT',
        r'OKLAHOMA\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── CT ────────────────────────────────────────────────────────────────────
    ("ct_pr1", [
        r'\bPR[-\s]*1\b.{0,40}(?:CONNECTICUT|CSP)',
        r'CONNECTICUT\s+(?:TRAFFIC\s+)?CRASH\s+REPORT',
        r'CONNECTICUT\s+(?:UNIFORM\s+POLICE\s+CRASH|MOTOR\s+VEHICLE\s+ACCIDENT)\s+REPORT',
        r'CONNECTICUT\s+STATE\s+POLICE\b',
    ]),

    # ── LA — DPSMV 2002 (current) and DOTD-390 (prior) ───────────────────────
    ("la_dotd390", [
        r'\bDPSMV[-\s]*2002\b',
        r'\bDOTD[-\s]*390\b',
        r'LOUISIANA\s+UNIFORM\s+MOTOR\s+VEHICLE',
        r'LOUISIANA\s+STATE\s+POLICE\b',
    ]),

    # ── UT — UDPS Crash (current) and SR-24 (prior) ──────────────────────────
    ("ut_sr24", [
        r'\bUDPS\b.{0,20}Crash',
        r'\bSR[-\s]*24\b.{0,40}(?:UTAH|UHP)',
        r"UTAH\s+INVESTIGATOR'?S\s+TRAFFIC",
        r'UTAH\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── MS ────────────────────────────────────────────────────────────────────
    ("ms_cr2", [
        r'\b(?:MISSISSIPPI\s+)?CR[-\s]*2\b.{0,40}(?:MISSISSIPPI|MHP|MDPS)',
        r'MISSISSIPPI\s+UNIFORM\s+CRASH\s+REPORT',
        r'MISSISSIPPI\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── AR — SR1-21 (current) and AR-40 (prior) ──────────────────────────────
    ("ar_crash", [
        r'\bSR[-\s]*1[-\s]*21\b',
        r'\bAR[-\s]*40\b.{0,40}(?:ARKANSAS|ASP)',
        r'ARKANSAS\s+MOTOR\s+VEHICLE\s+CRASH\s+REPORT',
        r'ARKANSAS\s+STATE\s+POLICE\b',
    ]),

    # ── IA — 433001 (current) and 432015 (prior) ─────────────────────────────
    ("ia_432015", [
        r'\b433001\b',
        r'\b432015\b',
        r"IOWA\s+INVESTIGATING\s+OFFICER'?S\s+REPORT",
        r'IOWA\s+STATE\s+PATROL\b',
    ]),

    # ── KS — Form 850 (current) and TRL-1 (prior) ────────────────────────────
    ("ks_trl1", [
        r'\bForm\s+850\b',
        r'\bTRL[-\s]*1\b',
        r'KANSAS\s+MOTOR\s+VEHICLE\s+ACCIDENT\s+REPORT',
        r'KANSAS\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── NV — NHP-1 ────────────────────────────────────────────────────────────
    ("nv_nhp1", [
        r'\bNHP[-\s]*1\b',
        r'NEVADA\s+(?:TRAFFIC\s+)?(?:ACCIDENT|CRASH)\s+REPORT',
        r'NEVADA\s+HIGHWAY\s+PATROL\b',
    ]),

    # ── MA — MA-RMV-CRASH ─────────────────────────────────────────────────────
    ("ma_cra43", [
        r'\bMA[-\s]*RMV[-\s]*CRASH\b',
        r'\bCRA[-\s]*43\b',
        r'COMMONWEALTH\s+OF\s+MASSACHUSETTS.{0,60}(?:CRASH|MOTOR\s+VEHICLE)',
        r'MASSACHUSETTS\s+(?:REGISTRY\s+OF\s+MOTOR\s+VEHICLES|STATE\s+POLICE)\b',
    ]),

    # ── AK ────────────────────────────────────────────────────────────────────
    ("ak_crash", [
        r'\b12[-\s]*234\b.{0,40}(?:ALASKA|AST)',
        r'ALASKA\s+STATE\s+TROOPERS\b',
        r'ALASKA\s+DIVISION\s+OF\s+MOTOR\s+VEHICLES\b',
    ]),

    # ── HI ────────────────────────────────────────────────────────────────────
    ("hi_hpd252", [
        r'\bHPD[-\s]*252\b',
        r'HAWAII\s+POLICE\s+DEPARTMENT.{0,40}(?:CRASH|REPORT)',
        r'HAWAII\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── ID ────────────────────────────────────────────────────────────────────
    ("id_itd3101", [
        r'\bITD[-\s]*3101\b',
        r'IDAHO\s+TRANSPORTATION\s+DEPARTMENT\b',
        r'IDAHO\s+STATE\s+POLICE\b.{0,40}(?:CRASH|REPORT)',
    ]),

    # ── ME ────────────────────────────────────────────────────────────────────
    ("me_crash", [
        r'MAINE\s+STATE\s+POLICE\b',
        r'MAINE\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── MT ────────────────────────────────────────────────────────────────────
    ("mt_crash", [
        r'MONTANA\s+HIGHWAY\s+PATROL\b',
        r'MONTANA\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── NE ────────────────────────────────────────────────────────────────────
    ("ne_310c", [
        r'\b310[-\s]*C\b.{0,40}(?:NEBRASKA|NSP)',
        r'NEBRASKA\s+STATE\s+PATROL\b',
        r'NEBRASKA\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── NH ────────────────────────────────────────────────────────────────────
    ("nh_dsmv311", [
        r'\bDSMV[-\s]*311\b',
        r'NEW\s+HAMPSHIRE\s+STATE\s+POLICE\b',
        r'NEW\s+HAMPSHIRE\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── NM ────────────────────────────────────────────────────────────────────
    ("nm_10516", [
        r'\b10[-\s]*516\b.{0,40}(?:NEW\s+MEXICO|NMSP)',
        r'NEW\s+MEXICO\s+STATE\s+POLICE\b',
        r'NEW\s+MEXICO\s+MOTOR\s+TRANSPORTATION\b',
    ]),

    # ── ND ────────────────────────────────────────────────────────────────────
    ("nd_sfn2086", [
        r'\bSFN[-\s]*2086\b',
        r'NORTH\s+DAKOTA\s+HIGHWAY\s+PATROL\b',
        r'NORTH\s+DAKOTA\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── RI ────────────────────────────────────────────────────────────────────
    ("ri_uc1", [
        r'\bUC[-\s]*1\b.{0,40}(?:RHODE\s+ISLAND|RISP)',
        r'RHODE\s+ISLAND\s+STATE\s+POLICE\b',
        r'RHODE\s+ISLAND\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── SD ────────────────────────────────────────────────────────────────────
    ("sd_crash", [
        r'SOUTH\s+DAKOTA\s+HIGHWAY\s+PATROL\b',
        r'SOUTH\s+DAKOTA\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── VT ────────────────────────────────────────────────────────────────────
    ("vt_tsp300", [
        r'\bTSP[-\s]*300\b',
        r'VERMONT\s+STATE\s+POLICE\b',
        r'VERMONT\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── WV ────────────────────────────────────────────────────────────────────
    ("wv_crash", [
        r'WEST\s+VIRGINIA\s+STATE\s+POLICE\b',
        r'WEST\s+VIRGINIA\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── WY ────────────────────────────────────────────────────────────────────
    ("wy_crash", [
        r'WYOMING\s+HIGHWAY\s+PATROL\b',
        r'WYOMING\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── DE ────────────────────────────────────────────────────────────────────
    ("de_tc308", [
        r'\bTC[-\s]*308\b',
        r'DELAWARE\s+STATE\s+POLICE\b',
        r'DELAWARE\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),

    # ── DC ────────────────────────────────────────────────────────────────────
    ("dc_mpd", [
        r'\bMPD[-\s]*P[-\s]*23\b',
        r'METROPOLITAN\s+POLICE\s+DEPARTMENT.{0,40}(?:DISTRICT\s+OF\s+COLUMBIA|DC)',
        r'DISTRICT\s+OF\s+COLUMBIA\s+(?:TRAFFIC\s+CRASH|ACCIDENT)\s+REPORT',
    ]),
]

# How many chars from the start of the document to scan.
CLASSIFIER_SCAN_CHARS = 8000


def classify_form(text: str) -> tuple[str, float]:
    """
    Identify which state form this document is.

    Args:
        text: Full extracted document text (only the first CLASSIFIER_SCAN_CHARS are used).

    Returns:
        (form_id, confidence)
    """
    header = text[:CLASSIFIER_SCAN_CHARS]

    for form_id, patterns in _FINGERPRINTS:
        for pattern in patterns:
            if re.search(pattern, header, re.IGNORECASE):
                return form_id, 0.95

    return "generic_mmucc", 0.40


def state_from_form_id(form_id: str) -> str | None:
    """Return 2-letter state abbreviation for a form_id, or None for generic."""
    _MAP = {
        "ca_chp555":    "CA",
        "tx_cr3":       "TX",
        "ny_mv104a":    "NY",
        "fl_hsmv":      "FL",
        "pa_aa600":     "PA",
        "oh_bmv2696":   "OH",
        "il_sr1":       "IL",
        "ga_sr13":      "GA",
        "nc_dmv349":    "NC",
        "nj_mv104":     "NJ",
        "mi_ud10":      "MI",
        "va_fr300":     "VA",
        "wa_422":       "WA",
        "az_40_8282":   "AZ",
        "co_dr2447":    "CO",
        "tn_cs0835":    "TN",
        "in_sr13":      "IN",
        "mo_1130":      "MO",
        "wi_mv4002":    "WI",
        "md_acrs":      "MD",
        "mn_bca403":    "MN",
        "sc_sr309":     "SC",
        "al_acrs":      "AL",
        "or_735":       "OR",
        "ky_le35a":     "KY",
        "ok_sr22":      "OK",
        "ct_pr1":       "CT",
        "la_dotd390":   "LA",
        "ut_sr24":      "UT",
        "ms_cr2":       "MS",
        "ar_crash":     "AR",
        "ia_432015":    "IA",
        "ks_trl1":      "KS",
        "nv_nhp1":      "NV",
        "ak_crash":     "AK",
        "hi_hpd252":    "HI",
        "id_itd3101":   "ID",
        "me_crash":     "ME",
        "ma_cra43":     "MA",
        "mt_crash":     "MT",
        "ne_310c":      "NE",
        "nh_dsmv311":   "NH",
        "nm_10516":     "NM",
        "nd_sfn2086":   "ND",
        "ri_uc1":       "RI",
        "sd_crash":     "SD",
        "vt_tsp300":    "VT",
        "wv_crash":     "WV",
        "wy_crash":     "WY",
        "de_tc308":     "DE",
        "dc_mpd":       "DC",
        "municipal_pd_collision": None,
        "generic_mmucc": None,
    }
    return _MAP.get(form_id)
