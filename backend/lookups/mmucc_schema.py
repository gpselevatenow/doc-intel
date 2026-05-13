"""
MMUCC 6th Edition (2024) canonical schema.

Source: NHTSA Model Minimum Uniform Crash Criteria, 6th Edition, 2024.
        https://www.nhtsa.gov/mmucc-1

Defines all 110 data elements across 4 categories:
  C = Crash/Event level
  V = Vehicle level
  P = Person level
  R = Roadway level

Each element: {
  "id":          "C01",
  "name":        "Crash Date",
  "category":    "Crash",
  "field_map":   "date_time",     # maps to our internal field_id
  "type":        "date",
  "required":    True,
  "codes":       {...}            # allowed values (if categorical)
}
"""
from __future__ import annotations

_ELEMENTS: dict[str, dict] = {

    # ══════════════════════════════════════════════════════════════════════
    # CATEGORY C — CRASH / EVENT LEVEL
    # ══════════════════════════════════════════════════════════════════════
    "C01": {"name": "Crash Date",                "category": "Crash",   "field_map": "date_time",    "type": "date",    "required": True,  "codes": {}},
    "C02": {"name": "Crash Time",                "category": "Crash",   "field_map": "date_time",    "type": "time",    "required": True,  "codes": {}},
    "C03": {"name": "County of Crash",           "category": "Crash",   "field_map": "location",     "type": "text",    "required": True,  "codes": {}},
    "C04": {"name": "City/Township of Crash",    "category": "Crash",   "field_map": "location",     "type": "text",    "required": True,  "codes": {}},
    "C05": {"name": "Trafficway Identifier",     "category": "Crash",   "field_map": "location",     "type": "text",    "required": True,  "codes": {}},
    "C06": {"name": "Milepoint",                 "category": "Crash",   "field_map": "location",     "type": "text",    "required": False, "codes": {}},
    "C07": {"name": "Latitude",                  "category": "Crash",   "field_map": None,           "type": "decimal", "required": False, "codes": {}},
    "C08": {"name": "Longitude",                 "category": "Crash",   "field_map": None,           "type": "decimal", "required": False, "codes": {}},
    "C09": {"name": "Manner of Collision",       "category": "Crash",   "field_map": "accident_type","type": "code",    "required": True,  "codes": {
        "1": "Not Collision Between Two Motor Vehicles in Transport",
        "2": "Rear-End",
        "3": "Head-On",
        "4": "Rear-to-Rear (Backing)",
        "5": "Angle",
        "6": "Sideswipe – Same Direction",
        "7": "Sideswipe – Opposite Direction",
        "8": "Single Vehicle",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "C10": {"name": "Weather",                   "category": "Crash",   "field_map": "weather",      "type": "code",    "required": True,  "codes": {
        "1": "Clear",
        "2": "Cloudy",
        "3": "Rain",
        "4": "Sleet, Hail",
        "5": "Snow",
        "6": "Fog, Smog, Smoke",
        "7": "Severe Crosswinds",
        "8": "Blowing Sand, Soil, Dirt",
        "10": "Freezing Rain or Drizzle",
        "11": "Blowing Snow",
        "12": "Other",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "C11": {"name": "Light Condition",           "category": "Crash",   "field_map": "light_condition","type": "code",   "required": True,  "codes": {
        "1": "Daylight",
        "2": "Dark – Not Lighted",
        "3": "Dark – Lighted",
        "4": "Dark – Unknown Lighting",
        "5": "Dawn",
        "6": "Dusk",
        "7": "Other",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "C12": {"name": "Road Surface Condition",    "category": "Crash",   "field_map": "road_surface",  "type": "code",   "required": True,  "codes": {
        "1": "Dry",
        "2": "Wet",
        "3": "Snow or Slush",
        "4": "Ice or Frost",
        "5": "Sand, Mud, Dirt, Gravel",
        "6": "Water (Standing, Moving)",
        "7": "Oil",
        "8": "Other",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "C13": {"name": "Type of Intersection",      "category": "Crash",   "field_map": None,            "type": "code",   "required": False, "codes": {
        "1": "Not an Intersection",
        "2": "Four-Way Intersection",
        "3": "T-Intersection",
        "4": "Y-Intersection",
        "5": "Traffic Circle or Roundabout",
        "6": "Five-Point or More",
        "7": "On Ramp",
        "8": "Off Ramp",
        "9": "Crossover",
        "10": "Railroad Grade Crossing",
        "11": "Shared-Use Path Crossing",
        "12": "Driveway or Alley",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "C14": {"name": "Relation to Junction",      "category": "Crash",   "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "C15": {"name": "Relation to Trafficway",    "category": "Crash",   "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "C16": {"name": "First Harmful Event",       "category": "Crash",   "field_map": "accident_type", "type": "code",   "required": True,  "codes": {
        "1":  "Overturn/Rollover",
        "2":  "Fire/Explosion",
        "3":  "Immersion or Partial Immersion",
        "4":  "Gas Inhalation",
        "5":  "Fell/Jumped from Vehicle",
        "6":  "Injured in Vehicle (Non-Collision)",
        "7":  "Other Non-Collision",
        "8":  "Pedestrian",
        "9":  "Pedalcyclist",
        "10": "Railway Vehicle",
        "11": "Live Animal",
        "12": "Motor Vehicle In-Transport",
        "14": "Parked Motor Vehicle",
        "15": "Non-Motorist on Personal Conveyance",
        "16": "Thrown or Falling Object",
        "17": "Boulder",
        "18": "Other Object (Not Fixed)",
        "19": "Building",
        "20": "Impact Attenuator/Crash Cushion",
        "21": "Bridge Overhead Structure",
        "22": "Bridge Pier or Support",
        "23": "Bridge Rail",
        "24": "Culvert",
        "25": "Curb",
        "26": "Ditch",
        "27": "Embankment",
        "28": "Guardrail Face",
        "29": "Guardrail End",
        "30": "Cable Barrier",
        "31": "Concrete Traffic Barrier",
        "32": "Other Traffic Barrier",
        "35": "Utility Pole/Light Support",
        "38": "Traffic Sign Support",
        "39": "Traffic Signal Support",
        "40": "Other Post, Pole or Support",
        "41": "Fence",
        "42": "Mailbox",
        "43": "Other Fixed Object",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "C17": {"name": "Most Harmful Event",        "category": "Crash",   "field_map": None,            "type": "code",   "required": True,  "codes": {}},  # Same codes as C16
    "C18": {"name": "Number of Motor Vehicles",  "category": "Crash",   "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "C19": {"name": "Number of Persons",         "category": "Crash",   "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "C20": {"name": "Agency Identifier (ORI)",   "category": "Crash",   "field_map": "agency",        "type": "text",   "required": True,  "codes": {}},
    "C21": {"name": "Case/Report Number",        "category": "Crash",   "field_map": "report_number", "type": "text",   "required": True,  "codes": {}},

    # ══════════════════════════════════════════════════════════════════════
    # CATEGORY V — VEHICLE LEVEL
    # ══════════════════════════════════════════════════════════════════════
    "V01": {"name": "Vehicle Number",            "category": "Vehicle", "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "V02": {"name": "Vehicle Identification Number (VIN)", "category": "Vehicle", "field_map": "vin", "type": "text",  "required": True,  "codes": {}},
    "V03": {"name": "Vehicle Year",              "category": "Vehicle", "field_map": "year",          "type": "integer","required": True,  "codes": {}},
    "V04": {"name": "Vehicle Make",              "category": "Vehicle", "field_map": "make",          "type": "text",   "required": True,  "codes": {}},
    "V05": {"name": "Vehicle Model",             "category": "Vehicle", "field_map": "model",         "type": "text",   "required": True,  "codes": {}},
    "V06": {"name": "Vehicle Body Type",         "category": "Vehicle", "field_map": None,            "type": "code",   "required": True,  "codes": {
        "01": "Passenger Car",
        "02": "Sport Utility Vehicle",
        "03": "Pickup Truck",
        "04": "Van (Mini, Full, Cargo)",
        "05": "Truck",
        "06": "Motorcycle",
        "07": "Moped or Motorized Bicycle",
        "08": "Bus",
        "09": "Other",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "V07": {"name": "Vehicle Color",             "category": "Vehicle", "field_map": "color",         "type": "text",   "required": False, "codes": {}},
    "V08": {"name": "License Plate Number",      "category": "Vehicle", "field_map": "plate",         "type": "text",   "required": True,  "codes": {}},
    "V09": {"name": "License Plate State",       "category": "Vehicle", "field_map": None,            "type": "text",   "required": True,  "codes": {}},
    "V10": {"name": "Vehicle Damage Extent",     "category": "Vehicle", "field_map": "damages",       "type": "code",   "required": True,  "codes": {
        "0": "No Damage",
        "2": "Minor Damage",
        "4": "Moderate Damage",
        "6": "Severe Damage",
        "8": "Totaled (Disabling Damage)",
        "9": "Unknown",
    }},
    "V11": {"name": "Damaged Areas",             "category": "Vehicle", "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "V12": {"name": "Vehicle Configuration",     "category": "Vehicle", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "V13": {"name": "Cargo Body Type",           "category": "Vehicle", "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "V14": {"name": "Hazardous Materials",       "category": "Vehicle", "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "V15": {"name": "Special Use",               "category": "Vehicle", "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "V16": {"name": "Emergency Use",             "category": "Vehicle", "field_map": None,            "type": "code",   "required": False, "codes": {
        "0": "Not in Emergency Use",
        "1": "Emergency Use",
        "9": "Unknown",
    }},
    "V17": {"name": "Trafficway Description",    "category": "Vehicle", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "V18": {"name": "Speed Limit",               "category": "Vehicle", "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "V19": {"name": "Vehicle Maneuver/Action",   "category": "Vehicle", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "V20": {"name": "Sequence of Events",        "category": "Vehicle", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "V21": {"name": "Contributing Circumstances – Vehicle", "category": "Vehicle", "field_map": None, "type": "code",   "required": False, "codes": {}},

    # ══════════════════════════════════════════════════════════════════════
    # CATEGORY P — PERSON LEVEL
    # ══════════════════════════════════════════════════════════════════════
    "P01": {"name": "Person Number",             "category": "Person",  "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "P02": {"name": "Person Type",               "category": "Person",  "field_map": "role",          "type": "code",   "required": True,  "codes": {
        "1": "Driver",
        "2": "Passenger",
        "3": "Pedestrian",
        "4": "Bicyclist",
        "5": "Other Cyclist",
        "6": "Person on Personal Conveyance",
        "7": "Unknown Occupant Type in Motor Vehicle",
        "8": "Occupant of Non-Motor Vehicle Transport Device",
        "9": "Unknown",
    }},
    "P03": {"name": "Age",                       "category": "Person",  "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "P04": {"name": "Sex",                       "category": "Person",  "field_map": None,            "type": "code",   "required": True,  "codes": {"1": "Male", "2": "Female", "9": "Unknown"}},
    "P05": {"name": "Injury Severity",           "category": "Person",  "field_map": "condition",     "type": "code",   "required": True,  "codes": {
        "O": "No Apparent Injury (O)",
        "C": "Possible Injury (C)",
        "B": "Suspected Minor Injury (B)",
        "A": "Suspected Serious Injury (A)",
        "K": "Fatal Injury (K)",
        "U": "Injured, Severity Unknown",
        "9": "Unknown",
    }},
    "P06": {"name": "Seating Position",          "category": "Person",  "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "P07": {"name": "Restraint System Use",      "category": "Person",  "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "P08": {"name": "Air Bag Deployed",          "category": "Person",  "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "P09": {"name": "Ejection",                  "category": "Person",  "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "P10": {"name": "Transported to Medical Facility", "category": "Person", "field_map": "transported_to", "type": "text", "required": False, "codes": {}},
    "P11": {"name": "Driver License Number",     "category": "Person",  "field_map": "license_number","type": "text",   "required": False, "codes": {}},
    "P12": {"name": "Driver License State",      "category": "Person",  "field_map": None,            "type": "text",   "required": False, "codes": {}},
    "P13": {"name": "Driver License Type",       "category": "Person",  "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "P14": {"name": "Contributing Circumstances – Person", "category": "Person", "field_map": "contributing_factors", "type": "code", "required": False, "codes": {
        "0":  "None",
        "1":  "Inattentive (Distracted)",
        "2":  "Careless/Reckless/Aggressive Driving",
        "3":  "Failure to Yield Right-of-Way",
        "4":  "Failure to Obey Traffic Signal/Sign",
        "5":  "Made Improper Turn",
        "6":  "Exceeding Authorized Speed Limit",
        "7":  "Driving at Unsafe Speed",
        "8":  "Operating Vehicle in Erratic, Reckless, Careless, Negligent, or Aggressive Manner",
        "9":  "Swerving or Avoiding: Due to Wind, Slippery Surface, Vehicle, Object, Non-Motorist in Roadway, Other Motor Vehicle",
        "10": "Over-Correcting/Over-Steering",
        "11": "Vision Obscured",
        "12": "Driver Fatigue",
        "13": "Under Influence of Alcohol, Drugs, or Medication",
        "14": "Illness",
        "15": "Physical Impairment",
        "98": "Not Reported",
        "99": "Unknown",
    }},
    "P15": {"name": "Non-Motorist Location",     "category": "Person",  "field_map": None,            "type": "code",   "required": False, "codes": {}},
    "P16": {"name": "Non-Motorist Action",       "category": "Person",  "field_map": None,            "type": "code",   "required": False, "codes": {}},

    # ══════════════════════════════════════════════════════════════════════
    # CATEGORY R — ROADWAY LEVEL
    # ══════════════════════════════════════════════════════════════════════
    "R01": {"name": "Roadway Function Class",    "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {
        "1":  "Rural – Principal Arterial – Interstate",
        "2":  "Rural – Principal Arterial – Other Freeways/Expressways",
        "6":  "Rural – Principal Arterial – Other",
        "7":  "Rural – Minor Arterial",
        "8":  "Rural – Major Collector",
        "9":  "Rural – Minor Collector",
        "19": "Rural – Local",
        "11": "Urban – Principal Arterial – Interstate",
        "12": "Urban – Principal Arterial – Other Freeways/Expressways",
        "14": "Urban – Principal Arterial – Other",
        "16": "Urban – Minor Arterial",
        "17": "Urban – Collector",
        "19": "Urban – Local",
    }},
    "R02": {"name": "Land Use",                  "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {"1": "Rural", "2": "Urban", "9": "Unknown"}},
    "R03": {"name": "Access Control",            "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "R04": {"name": "Trafficway Description (Road)", "category": "Roadway", "field_map": None,        "type": "code",   "required": True,  "codes": {
        "1": "Two-Way, Not Divided",
        "2": "Two-Way, Divided, Unprotected (Painted > 4 ft) Median",
        "3": "Two-Way, Divided, Positive Median Barrier",
        "4": "One-Way Trafficway",
        "5": "Not Physically Divided (Two-Way Roadways Only)",
        "6": "Entrance/Exit Ramp",
        "9": "Unknown",
    }},
    "R05": {"name": "Speed Limit",               "category": "Roadway", "field_map": None,            "type": "integer","required": True,  "codes": {}},
    "R06": {"name": "Roadway Alignment",         "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "R07": {"name": "Roadway Grade",             "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "R08": {"name": "Roadway Surface Type",      "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "R09": {"name": "Roadway Surface Condition", "category": "Roadway", "field_map": "road_surface",  "type": "code",   "required": True,  "codes": {}},
    "R10": {"name": "Traffic Control Device",    "category": "Roadway", "field_map": None,            "type": "code",   "required": True,  "codes": {}},
    "R11": {"name": "Traffic Control Device Functioning", "category": "Roadway", "field_map": None,   "type": "code",   "required": True,  "codes": {}},
}

# Field map index: internal field_id → list of MMUCC element IDs
_FIELD_MAP_INDEX: dict[str, list[str]] = {}
for _eid, _elem in _ELEMENTS.items():
    fm = _elem.get("field_map")
    if fm:
        _FIELD_MAP_INDEX.setdefault(fm, []).append(_eid)


def field(element_id: str) -> dict | None:
    """Return MMUCC element descriptor for an element ID (e.g. 'C09'), or None."""
    return _ELEMENTS.get(element_id.upper())


def decode(element_id: str, code: str) -> str:
    """
    Decode a coded MMUCC value to its human-readable label.
    Returns the raw code if no mapping exists.
    """
    elem = _ELEMENTS.get(element_id.upper())
    if not elem:
        return code
    return elem.get("codes", {}).get(str(code).strip(), code)


def elements_for_field(field_id: str) -> list[str]:
    """Return list of MMUCC element IDs that map to an internal field_id."""
    return _FIELD_MAP_INDEX.get(field_id, [])


def required_elements() -> list[str]:
    """Return list of element IDs marked required=True."""
    return [eid for eid, e in _ELEMENTS.items() if e.get("required")]
