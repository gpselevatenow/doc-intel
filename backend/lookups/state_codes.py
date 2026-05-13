"""
Per-state coded-value lookup tables for all 50 US states + DC crash reports.

decode(state, table, code) is the main entry point.

Most states follow MMUCC (Model Minimum Uniform Crash Criteria) standard codes.
Custom tables are only provided where a state uses non-MMUCC coding.
"""
from __future__ import annotations

# ── MMUCC standard tables (shared by most states) ─────────────────────────────
# These are used as defaults for states that do not override them.

_MMUCC_WEATHER: dict[str, str] = {
    "1": "Clear", "2": "Cloudy", "3": "Rain", "4": "Sleet/Hail",
    "5": "Snow", "6": "Fog/Smog/Smoke", "7": "Blowing Sand/Soil/Dirt/Snow",
    "8": "Severe Crosswinds", "9": "Other / Unknown",
}

_MMUCC_LIGHT_CONDITION: dict[str, str] = {
    "1": "Daylight", "2": "Dark – Lighted", "3": "Dark – Not Lighted",
    "4": "Dark – Unknown Lighting", "5": "Dawn", "6": "Dusk", "99": "Other / Unknown",
}

_MMUCC_ACCIDENT_TYPE: dict[str, str] = {
    "1": "Not Collision Between Two Motor Vehicles",
    "2": "Rear End", "3": "Head On", "4": "Rear to Rear",
    "5": "Angle", "6": "Sideswipe – Same Direction",
    "7": "Sideswipe – Opposite Direction", "8": "Other",
}

_MMUCC_ROAD_SURFACE: dict[str, str] = {
    "1": "Dry", "2": "Wet", "3": "Snow/Slush", "4": "Ice",
    "5": "Sand/Mud/Dirt/Oil/Gravel", "6": "Water – Standing/Moving", "9": "Other",
}

_MMUCC_INJURY_SEVERITY: dict[str, str] = {
    "K": "Killed (Fatal)",
    "A": "Suspected Serious Injury",
    "B": "Suspected Minor Injury",
    "C": "Possible Injury",
    "O": "Not Injured",
}

_MMUCC_CONTRIBUTING_FACTORS: dict[str, str] = {
    "1":  "Failed to Control Speed",
    "2":  "Failed to Drive in Single Lane",
    "3":  "Failed to Yield Right of Way – Stop Sign",
    "4":  "Failed to Yield Right of Way – Open Intersection",
    "5":  "Failed to Yield Right of Way – Private Drive",
    "6":  "Failed to Yield Right of Way – Emergency Vehicle",
    "7":  "Turned When Unsafe",
    "8":  "Changed Lane When Unsafe",
    "9":  "Changed Lane Without Signal",
    "10": "Passed in No-Passing Zone",
    "11": "Drove Left of Center",
    "12": "Ran Off Road",
    "13": "Followed Too Closely",
    "14": "Ran Red Light",
    "15": "Disregarded Stop and Go Signal",
    "16": "Disregarded Warning Sign",
    "17": "Drove Without Headlights",
    "18": "Failed to Stop at Proper Place",
    "19": "Improper Backing",
    "20": "Wrong Way – One Way Road",
    "21": "Distraction in Vehicle",
    "22": "Driver Inattention",
    "24": "Cell/Mobile Device Use – Talking/Text",
    "25": "Pedestrian Failed to Yield Right of Way",
    "26": "Pedestrian/Cyclist – Inattention",
    "28": "Alcohol",
    "29": "Drugs",
    "30": "Fatigue/Asleep",
    "31": "Defective Brakes or Lights",
    "32": "Under-Inflated Tire(s)",
    "33": "Obstruction in Road",
    "34": "Slick or Loose Surface",
    "35": "Road Under Construction or Maintenance",
    "36": "Inadequate Lane Width",
    "37": "Inadequate Sight Distance",
    "44": "Speed in Excess of Posted Speed Limit",
    "51": "Unsafe Speed",
    "96": "No Contributing Factor",
    "99": "Other / Unknown",
}

# A standard MMUCC block assembled for states that use it directly.
_MMUCC_STANDARD: dict[str, dict[str, str]] = {
    "weather":              _MMUCC_WEATHER,
    "light_condition":      _MMUCC_LIGHT_CONDITION,
    "accident_type":        _MMUCC_ACCIDENT_TYPE,
    "road_surface":         _MMUCC_ROAD_SURFACE,
    "injury_severity":      _MMUCC_INJURY_SEVERITY,
    "contributing_factors": _MMUCC_CONTRIBUTING_FACTORS,
}

# ── TX CR-3 ────────────────────────────────────────────────────────────────────

_TX: dict[str, dict[str, str]] = {
    "weather": {
        "1": "Clear", "2": "Cloudy", "3": "Rain", "4": "Sleet/Hail",
        "5": "Snow", "6": "Fog/Smog/Smoke", "7": "Blowing Sand/Soil/Dirt/Snow",
        "8": "Severe Crosswinds", "9": "Other / Unknown",
    },
    "light_condition": {
        "1": "Daylight", "2": "Dark – Lighted", "3": "Dark – Not Lighted",
        "4": "Dark – Unknown Lighting", "5": "Dawn", "6": "Dusk", "99": "Other / Unknown",
    },
    "accident_type": {
        "1": "Not Collision Between Two Motor Vehicles",
        "2": "Rear End", "3": "Head On", "4": "Rear to Rear",
        "5": "Angle", "6": "Sideswipe – Same Direction",
        "7": "Sideswipe – Opposite Direction", "8": "Other",
    },
    "road_surface": {
        "1": "Dry", "2": "Wet", "3": "Snow", "4": "Ice",
        "5": "Sand/Mud/Dirt/Oil/Gravel", "6": "Other",
    },
    "road_type": {
        "1": "Two-Way, Not Divided", "2": "Two-Way, Divided, Unprotected Median",
        "3": "Two-Way, Divided, Positive Median Barrier", "4": "One-Way", "5": "Other",
    },
    "injury_severity": {
        "K": "Killed (Fatal)",
        "A": "Suspected Serious Injury",
        "B": "Suspected Minor Injury",
        "C": "Possible Injury",
        "O": "Not Injured",
    },
    "contributing_factors": {
        "1":  "Failed to Control Speed",
        "2":  "Failed to Drive in Single Lane",
        "3":  "Failed to Yield Right of Way – Stop Sign",
        "4":  "Failed to Yield Right of Way – Open Intersection",
        "5":  "Failed to Yield Right of Way – Private Drive",
        "6":  "Failed to Yield Right of Way – Emergency Vehicle",
        "7":  "Turned When Unsafe",
        "8":  "Changed Lane When Unsafe",
        "9":  "Changed Lane Without Signal",
        "10": "Passed in No-Passing Zone",
        "11": "Drove Left of Center",
        "12": "Ran Off Road",
        "13": "Followed Too Closely",
        "14": "Ran Red Light",
        "15": "Disregarded Stop and Go Signal",
        "16": "Disregarded Warning Sign at Construction/Maintenance Zone",
        "17": "Drove Without Headlights",
        "18": "Failed to Stop at Proper Place",
        "19": "Improper Backing",
        "20": "Wrong Way – One Way Road",
        "21": "Distraction in Vehicle",
        "22": "Driver Inattention",
        "24": "Cell/Mobile Device Use – Talking/Text",
        "25": "Pedestrian Failed to Yield Right of Way",
        "26": "Pedestrian/Cyclist – Inattention",
        "28": "Alcohol",
        "29": "Drugs",
        "30": "Fatigue/Asleep",
        "31": "Defective Brakes or Lights",
        "32": "Under-Inflated Tire(s)",
        "33": "Obstruction in Road",
        "34": "Slick or Loose Surface",
        "35": "Road Under Construction or Maintenance",
        "36": "Inadequate Lane Width",
        "37": "Inadequate Sight Distance",
        "44": "Speed in Excess of Posted Speed Limit",
        "51": "Unsafe Speed",
        "96": "No Contributing Factor",
        "99": "Other / Unknown",
    },
    "vehicle_type": {
        "1": "Passenger Car", "2": "Pickup Truck", "3": "Van/SUV",
        "4": "Commercial Truck/Semi", "5": "Motorcycle", "6": "Bus",
        "7": "Farm Equipment", "8": "Construction Equipment",
        "9": "Other", "99": "Unknown",
    },
}

# ── FL HSMV 90010 ──────────────────────────────────────────────────────────────

_FL: dict[str, dict[str, str]] = {
    "accident_type": {
        "01": "Rear-End", "02": "Head-On", "03": "Angle",
        "04": "Sideswipe – Same Direction", "05": "Sideswipe – Opposite Direction",
        "06": "Rear-to-Rear", "07": "Single Vehicle", "08": "Left Turn",
        "09": "Right Turn", "10": "Backing", "11": "Pedestrian",
        "12": "Bicycle/Pedalcycle", "13": "Left Turn/U-Turn",
        "14": "Sideswipe, Not Otherwise Specified", "99": "Other / Unknown",
    },
    "first_harmful_event": {
        "01": "Overturn/Rollover", "02": "Fire/Explosion",
        "03": "Immersion in Water", "04": "Gas Inhalation",
        "05": "Falls in Transport", "06": "Jackknife",
        "07": "Cargo Loss or Shift", "08": "Equipment Failure",
        "09": "Separation of Units",
        "10": "Ran Off Road – Right", "11": "Ran Off Road – Left",
        "12": "Cross Median or Centerline",
        "13": "Downhill Runaway", "14": "Vehicle in Path (Same Direction)",
        "15": "Vehicle in Path (Opposite Direction)", "16": "Parked Motor Vehicle",
        "17": "Pedalcycle", "18": "Pedestrian", "19": "Railway Train",
        "20": "Animal", "21": "Fixed Object", "22": "Other Object",
        "99": "Other",
    },
    "contributing_factors": {
        "1":  "None", "2":  "Alcohol", "3":  "Drugs",
        "4":  "Failure to Yield", "5":  "Careless Driving",
        "6":  "Ran Red Light", "7":  "Ran Stop Sign",
        "8":  "Exceeded Speed Limit", "9":  "Wrong Side of Road",
        "10": "Improper Lane Change", "11": "Followed Too Closely",
        "12": "Improper Turning", "13": "Improper Backing",
        "14": "Fatigue or Asleep", "15": "Distracted – Electronic Device",
        "16": "Driving Wrong Way", "17": "Pedestrian – Failure to Yield",
        "18": "Pedestrian – Inattentive", "99": "Other",
    },
    "injury_severity": {
        "1": "None", "2": "Possible Injury", "3": "Non-Incapacitating",
        "4": "Incapacitating", "5": "Fatal",
    },
    "weather": {
        "1": "Clear", "2": "Cloudy", "3": "Rain", "4": "Fog",
        "5": "Sleet/Hail", "6": "Blowing Sand/Soil/Dirt",
        "7": "Severe Crosswind", "8": "Blowing Snow", "9": "Other",
    },
}

# ── CA CHP 555 ─────────────────────────────────────────────────────────────────

_CA: dict[str, dict[str, str]] = {
    "accident_type": {
        "A": "Head-On", "B": "Sideswipe", "C": "Rear End",
        "D": "Broadside", "E": "Hit Object", "F": "Overturned",
        "G": "Vehicle/Pedestrian", "H": "Other",
    },
    "weather": {
        "A": "Clear", "B": "Cloudy", "C": "Raining", "D": "Snowing",
        "E": "Fog", "F": "Other", "G": "Wind",
    },
    "road_surface": {
        "A": "Dry", "B": "Wet", "C": "Snowy or Icy",
        "D": "Slippery (Muddy, Oily, etc.)", "E": "Other",
    },
    "light_condition": {
        "A": "Daylight", "B": "Dusk or Dawn",
        "C": "Dark – Street Lights", "D": "Dark – No Street Lights",
        "E": "Dark – Street Lights Not Functioning",
    },
    "injury_severity": {
        "1": "Fatal", "2": "Injury (Severe)",
        "3": "Injury (Other Visible)", "4": "Complaint of Pain",
    },
    "vehicle_type": {
        "A": "Passenger Car", "B": "Pickup or Panel Truck",
        "C": "Truck or Truck Tractor", "D": "Motorcycle/Scooter",
        "E": "Bicycle", "F": "Other Motor Vehicle", "G": "Other Vehicle",
    },
}

# ── NY MV-104A ─────────────────────────────────────────────────────────────────

_NY: dict[str, dict[str, str]] = {
    "accident_type": {
        "1":  "Rear-End", "2":  "Head-On", "3":  "Angle",
        "4":  "Sideswipe – Same Direction", "5":  "Sideswipe – Opposite Direction",
        "6":  "Left Turn", "7":  "Right Turn", "8":  "Left Turn – Head-On",
        "9":  "Single Vehicle", "10": "Backing", "11": "Pedestrian",
        "12": "Cyclist", "13": "Rear-to-Rear", "99": "Unknown",
    },
    "weather": {
        "1": "Clear", "2": "Cloudy", "3": "Rain", "4": "Snow",
        "5": "Fog/Smog/Smoke", "6": "Sleet/Hail/Freezing Rain",
        "7": "Severe Crosswinds", "8": "Blowing Sand/Soil",
        "9": "Other", "10": "Unknown",
    },
    "light_condition": {
        "1": "Daylight", "2": "Dawn", "3": "Dusk",
        "4": "Dark – Street Lights On", "5": "Dark – Street Lights Off",
        "6": "Dark – No Street Lights", "7": "Other",
    },
    "injury_severity": {
        "1": "Killed", "2": "Serious Injury",
        "3": "Moderate Injury", "4": "Minor Injury",
        "5": "No Injury",
    },
}

# ── PA AA-600 ──────────────────────────────────────────────────────────────────

_PA: dict[str, dict[str, str]] = {
    "accident_type": {
        "01": "Not a Collision between Motor Vehicles in Transport",
        "02": "Rear-End", "03": "Head-On", "04": "Rear-to-Rear (Backing)",
        "05": "Angle", "06": "Sideswipe – Same Direction",
        "07": "Sideswipe – Opposite Direction", "99": "Other",
    },
    "weather": {
        "1": "Clear/Partly Cloudy", "2": "Cloudy", "3": "Fog/Smog/Smoke",
        "4": "Rain", "5": "Sleet/Hail/Freezing Rain/Drizzle",
        "6": "Snow", "7": "Severe Crosswinds",
        "8": "Blowing Sand/Soil/Dirt/Snow", "9": "Other",
    },
    "light_condition": {
        "1": "Daylight", "2": "Dark – Lighted", "3": "Dark – Not Lighted",
        "4": "Dark – Unknown Lighting", "5": "Dawn", "6": "Dusk", "7": "Other",
    },
    "road_surface": {
        "1": "Dry", "2": "Wet", "3": "Sand/Mud/Dirt/Oil/Gravel",
        "4": "Snow/Slush", "5": "Ice", "6": "Ice Patches",
        "7": "Water – Standing/Moving", "9": "Other",
    },
    "injury_severity": {
        "0": "No Apparent Injury", "1": "Minor Injury",
        "2": "Moderate Injury", "3": "Serious Injury", "4": "Fatal",
    },
    "vehicle_type": {
        "01": "Passenger Car", "02": "Motorcycle", "03": "Pedalcycle",
        "04": "Small Truck (GVWR < 10,000 lbs)",
        "05": "Medium Truck (10,001–26,000 lbs)",
        "06": "Large Truck/Tractor-Trailer",
        "07": "Bus", "08": "Van", "09": "SUV", "10": "Pickup Truck",
        "11": "Other", "12": "Unknown",
    },
}

# ── OH BMV-2696 ────────────────────────────────────────────────────────────────
# Ohio uses MMUCC standard with minor additions.
_OH = dict(_MMUCC_STANDARD)

# ── IL SR-1 ────────────────────────────────────────────────────────────────────
_IL = dict(_MMUCC_STANDARD)

# ── GA SR-13A ──────────────────────────────────────────────────────────────────
_GA = dict(_MMUCC_STANDARD)

# ── NC DMV-349 ─────────────────────────────────────────────────────────────────
_NC = dict(_MMUCC_STANDARD)

# ── NJ MV-104 ─────────────────────────────────────────────────────────────────
_NJ = dict(_MMUCC_STANDARD)

# ── MI UD-10 ───────────────────────────────────────────────────────────────────
_MI = dict(_MMUCC_STANDARD)

# ── VA FR-300 ──────────────────────────────────────────────────────────────────
_VA = dict(_MMUCC_STANDARD)

# ── WA Form 422 ────────────────────────────────────────────────────────────────
_WA = dict(_MMUCC_STANDARD)

# ── AZ 40-8282 ─────────────────────────────────────────────────────────────────
_AZ = dict(_MMUCC_STANDARD)

# ── CO DR 2447 ─────────────────────────────────────────────────────────────────
_CO = dict(_MMUCC_STANDARD)

# ── TN CS-0835 ─────────────────────────────────────────────────────────────────
_TN = dict(_MMUCC_STANDARD)

# ── IN SR-13 ───────────────────────────────────────────────────────────────────
_IN = dict(_MMUCC_STANDARD)

# ── MO Form 1130 ───────────────────────────────────────────────────────────────
_MO = dict(_MMUCC_STANDARD)

# ── WI MV4002 ──────────────────────────────────────────────────────────────────
_WI = dict(_MMUCC_STANDARD)

# ── MD ACRS ────────────────────────────────────────────────────────────────────
_MD = dict(_MMUCC_STANDARD)

# ── MN BCA-403 ─────────────────────────────────────────────────────────────────
_MN = dict(_MMUCC_STANDARD)

# ── SC SR-309 ──────────────────────────────────────────────────────────────────
_SC = dict(_MMUCC_STANDARD)

# ── AL ACRS ────────────────────────────────────────────────────────────────────
_AL = dict(_MMUCC_STANDARD)

# ── OR 735-6000 ────────────────────────────────────────────────────────────────
_OR = dict(_MMUCC_STANDARD)

# ── KY LE-35A ─────────────────────────────────────────────────────────────────
_KY = dict(_MMUCC_STANDARD)

# ── OK SR-22 ───────────────────────────────────────────────────────────────────
_OK = dict(_MMUCC_STANDARD)

# ── CT PR-1 ────────────────────────────────────────────────────────────────────
_CT = dict(_MMUCC_STANDARD)

# ── LA DOTD-390 ────────────────────────────────────────────────────────────────
_LA = dict(_MMUCC_STANDARD)

# ── UT SR-24 ───────────────────────────────────────────────────────────────────
_UT = dict(_MMUCC_STANDARD)

# ── MS CR-2 ────────────────────────────────────────────────────────────────────
_MS = dict(_MMUCC_STANDARD)

# ── AR ─────────────────────────────────────────────────────────────────────────
_AR = dict(_MMUCC_STANDARD)

# ── IA ─────────────────────────────────────────────────────────────────────────
_IA = dict(_MMUCC_STANDARD)

# ── KS ─────────────────────────────────────────────────────────────────────────
_KS = dict(_MMUCC_STANDARD)

# ── AK ─────────────────────────────────────────────────────────────────────────
_AK = dict(_MMUCC_STANDARD)

# ── HI ─────────────────────────────────────────────────────────────────────────
_HI = dict(_MMUCC_STANDARD)

# ── ID ─────────────────────────────────────────────────────────────────────────
_ID = dict(_MMUCC_STANDARD)

# ── ME ─────────────────────────────────────────────────────────────────────────
_ME = dict(_MMUCC_STANDARD)

# ── MA ─────────────────────────────────────────────────────────────────────────
_MA = dict(_MMUCC_STANDARD)

# ── MT ─────────────────────────────────────────────────────────────────────────
_MT = dict(_MMUCC_STANDARD)

# ── NE ─────────────────────────────────────────────────────────────────────────
_NE = dict(_MMUCC_STANDARD)

# ── NH ─────────────────────────────────────────────────────────────────────────
_NH = dict(_MMUCC_STANDARD)

# ── NM ─────────────────────────────────────────────────────────────────────────
_NM = dict(_MMUCC_STANDARD)

# ── ND ─────────────────────────────────────────────────────────────────────────
_ND = dict(_MMUCC_STANDARD)

# ── RI ─────────────────────────────────────────────────────────────────────────
_RI = dict(_MMUCC_STANDARD)

# ── SD ─────────────────────────────────────────────────────────────────────────
_SD = dict(_MMUCC_STANDARD)

# ── VT ─────────────────────────────────────────────────────────────────────────
_VT = dict(_MMUCC_STANDARD)

# ── WV ─────────────────────────────────────────────────────────────────────────
_WV = dict(_MMUCC_STANDARD)

# ── WY ─────────────────────────────────────────────────────────────────────────
_WY = dict(_MMUCC_STANDARD)

# ── DE ─────────────────────────────────────────────────────────────────────────
_DE = dict(_MMUCC_STANDARD)

# ── DC ─────────────────────────────────────────────────────────────────────────
_DC = dict(_MMUCC_STANDARD)

# ── Registry ──────────────────────────────────────────────────────────────────
_STATE_TABLES: dict[str, dict[str, dict[str, str]]] = {
    # Original 5
    "TX": _TX, "tx_cr3":       _TX,
    "FL": _FL, "fl_hsmv":      _FL,
    "CA": _CA, "ca_chp555":    _CA,
    "NY": _NY, "ny_mv104a":    _NY,
    "PA": _PA, "pa_aa600":     _PA,
    # Tier 1
    "OH": _OH, "oh_bmv2696":   _OH,
    "IL": _IL, "il_sr1":       _IL,
    "GA": _GA, "ga_sr13":      _GA,
    "NC": _NC, "nc_dmv349":    _NC,
    "NJ": _NJ, "nj_mv104":     _NJ,
    "MI": _MI, "mi_ud10":      _MI,
    "VA": _VA, "va_fr300":     _VA,
    "WA": _WA, "wa_422":       _WA,
    "AZ": _AZ, "az_40_8282":   _AZ,
    "CO": _CO, "co_dr2447":    _CO,
    # Tier 2
    "TN": _TN, "tn_cs0835":    _TN,
    "IN": _IN, "in_sr13":      _IN,
    "MO": _MO, "mo_1130":      _MO,
    "WI": _WI, "wi_mv4002":    _WI,
    "MD": _MD, "md_acrs":      _MD,
    "MN": _MN, "mn_bca403":    _MN,
    "SC": _SC, "sc_sr309":     _SC,
    "AL": _AL, "al_acrs":      _AL,
    "OR": _OR, "or_735":       _OR,
    "KY": _KY, "ky_le35a":     _KY,
    "OK": _OK, "ok_sr22":      _OK,
    "CT": _CT, "ct_pr1":       _CT,
    "LA": _LA, "la_dotd390":   _LA,
    "UT": _UT, "ut_sr24":      _UT,
    "MS": _MS, "ms_cr2":       _MS,
    # Tier 3
    "AR": _AR, "ar_crash":     _AR,
    "IA": _IA, "ia_432015":    _IA,
    "KS": _KS, "ks_trl1":      _KS,
    "AK": _AK, "ak_crash":     _AK,
    "HI": _HI, "hi_hpd252":    _HI,
    "ID": _ID, "id_itd3101":   _ID,
    "ME": _ME, "me_crash":     _ME,
    "MA": _MA, "ma_cra43":     _MA,
    "MT": _MT, "mt_crash":     _MT,
    "NE": _NE, "ne_310c":      _NE,
    "NH": _NH, "nh_dsmv311":   _NH,
    "NM": _NM, "nm_10516":     _NM,
    "ND": _ND, "nd_sfn2086":   _ND,
    "RI": _RI, "ri_uc1":       _RI,
    "SD": _SD, "sd_crash":     _SD,
    "VT": _VT, "vt_tsp300":    _VT,
    "WV": _WV, "wv_crash":     _WV,
    "WY": _WY, "wy_crash":     _WY,
    "DE": _DE, "de_tc308":     _DE,
    "DC": _DC, "dc_mpd":       _DC,
}


def decode(state: str, table: str, code: str) -> str:
    """
    Decode a coded field value for a given state and table name.
    Returns the human-readable label, or the raw code if not found.

    Args:
        state:  State abbreviation or form_id (e.g. "TX", "tx_cr3")
        table:  Table name matching internal field_id (e.g. "weather", "accident_type")
        code:   Raw code string from extracted field
    """
    tables = _STATE_TABLES.get(state.upper()) or _STATE_TABLES.get(state.lower())
    if not tables:
        return code
    lookup = tables.get(table, {})
    if not lookup:
        return code
    # Handle multi-value codes (comma/semicolon separated)
    parts = [p.strip() for p in code.replace(";", ",").split(",") if p.strip()]
    decoded = [lookup.get(p, p) for p in parts]
    return ", ".join(decoded) if decoded else code


def tables_for_state(state: str) -> list[str]:
    """Return list of available table names for a state."""
    key = state.upper() if state.upper() in _STATE_TABLES else state.lower()
    return list(_STATE_TABLES.get(key, {}).keys())
