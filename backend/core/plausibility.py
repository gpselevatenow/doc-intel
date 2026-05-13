"""Field-specific value plausibility checks — Component 5 of revised scoring.

Each function returns 0.0–1.0:
  1.0  value clearly fits the field's semantic type
  0.5  uncertain / no registered function for this field
  0.2  value clearly does not fit (wrong shape, out-of-range date, etc.)

These are SEMANTIC checks, complementary to (and distinct from) template
validators, which are syntactic hard filters.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Callable

_CURRENT_YEAR = datetime.now().year

# ── Date plausibility ─────────────────────────────────────────────────

_DATE_PATTERNS = [
    re.compile(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b'),
    re.compile(r'\b\d{4}[/\-]\d{2}[/\-]\d{2}\b'),
    re.compile(
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b',
        re.I,
    ),
    re.compile(
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',
        re.I,
    ),
    re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b', re.I),
]

_YEAR_RE = re.compile(r'\b((?:19|20)\d{2})\b')


def _plausibility_date(value: str) -> float:
    value = value.strip()
    has_date = any(p.search(value) for p in _DATE_PATTERNS)
    m = _YEAR_RE.search(value)
    year = int(m.group(1)) if m else None

    if not has_date:
        # Still give partial credit if there are digits that look date-like
        if re.search(r'\d{4}', value) or re.search(r'\d{1,2}/\d{1,2}', value):
            return 0.4
        return 0.2

    if year is None:
        return 0.5  # looks like a date, no year found
    if 1990 <= year <= _CURRENT_YEAR + 1:
        return 1.0
    if 1970 <= year <= 2040:
        return 0.5  # plausible year, just outside normal crash report range
    return 0.2


# ── Report number plausibility ────────────────────────────────────────

def _plausibility_report_number(value: str) -> float:
    value = value.strip()
    if not (4 <= len(value) <= 40):
        return 0.3
    # Structured format: XX-YYYY-NNNNNN  or  FWPD-YY-MM-DD-NNNN
    if re.match(r'^[A-Z]{2,6}[-/]\d{2,4}[-/]\d{2,10}', value):
        return 1.0
    if re.match(r'^[A-Za-z0-9\-/#]{4,40}$', value):
        return 0.8
    return 0.4


# ── VIN plausibility ──────────────────────────────────────────────────

def _plausibility_vin(value: str) -> float:
    # TODO: implement ISO-3779 position-9 checksum
    v = value.strip().upper()
    if len(v) != 17:
        return 0.2
    if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', v):
        return 1.0  # no I, O, Q — valid VIN charset
    if re.match(r'^[A-Z0-9]{17}$', v):
        return 0.7  # right length but contains I/O/Q
    return 0.4


# ── Year plausibility ─────────────────────────────────────────────────

def _plausibility_year(value: str) -> float:
    m = re.match(r'^\s*(\d{4})\s*$', value.strip())
    if not m:
        return 0.3
    yr = int(m.group(1))
    if 1990 <= yr <= _CURRENT_YEAR + 1:
        return 1.0
    return 0.2


# ── Weather plausibility ──────────────────────────────────────────────

_WEATHER_TERMS = frozenset({
    "clear", "rain", "rainy", "raining", "snow", "snowing", "snowy", "sleet",
    "hail", "hailing", "fog", "foggy", "cloud", "cloudy", "overcast", "mist",
    "misty", "drizzle", "drizzling", "storm", "thunderstorm", "thunder",
    "sunny", "ice", "icy", "blowing", "smoke", "smog", "dust", "sand",
    "wind", "windy", "partly",
})


def _plausibility_weather(value: str) -> float:
    lower = value.strip().lower()
    if any(t in lower for t in _WEATHER_TERMS):
        return 1.0
    if re.search(r'\d', lower):  # contains digits → probably not a weather description
        return 0.3
    return 0.4


# ── Light condition plausibility ──────────────────────────────────────

_LIGHT_TERMS = frozenset({
    "daylight", "dusk", "dawn", "dark", "night", "lighted", "unlighted",
    "unknown lighting", "day", "dusk", "dawn", "noon", "afternoon",
})


def _plausibility_light_condition(value: str) -> float:
    lower = value.strip().lower()
    if any(t in lower for t in _LIGHT_TERMS):
        return 1.0
    if re.search(r'\d', lower):
        return 0.3
    return 0.4


# ── Person name plausibility ──────────────────────────────────────────

def _plausibility_person_name(value: str) -> float:
    value = value.strip()
    if not (3 <= len(value) <= 80):
        return 0.3
    words = value.split()
    if not (2 <= len(words) <= 6):
        return 0.4
    proper = sum(
        1 for w in words
        if re.match(r'^[A-Z][a-z\'.\-]+$', w) or re.match(r'^[A-Z]{1,3}\.?$', w)
    )
    if proper >= 2:
        return 1.0
    if re.search(r'[A-Za-z]{2}', value):
        return 0.6
    return 0.3


# ── Location plausibility ─────────────────────────────────────────────

_ROAD_TERMS = re.compile(
    r'\b(?:highway|hwy|interstate|i-\d|route|rd|road|street|st|avenue|ave|'
    r'blvd|boulevard|drive|dr|lane|ln|parkway|pkwy|freeway|fwy|'
    r'mile\s*marker|mm\s*\d|exit\s*\d|northbound|southbound|eastbound|westbound|'
    r'nb|sb|eb|wb)\b',
    re.I,
)

_INTERSECTION_TERMS = re.compile(
    r'\b(?:at\s+intersection|intersection|cross\s*street|and\s+[a-z]|'
    r'&\s+[a-z]|at\s+[a-z]|between|junction|jct)\b',
    re.I,
)

_OCR_GARBAGE_RE = re.compile(
    r'(?:[A-Za-z][A-Z][a-z]){2,}|'   # mixed-case runs: "MMileil"
    r'[^a-zA-Z0-9\s\-/.,()#\']{3,}|' # 3+ consecutive non-word chars
    r'\b[a-z]+[A-Z][a-z]+[A-Z][a-z]' # internal uppercase run
)


def _plausibility_location(value: str) -> float:
    v = value.strip()
    n = len(v)
    if n < 10 or n > 200:
        return 0.2

    has_road = bool(_ROAD_TERMS.search(v))
    has_intersection = bool(_INTERSECTION_TERMS.search(v))
    has_garbage = bool(_OCR_GARBAGE_RE.search(v))
    starts_punct = bool(re.match(r'^[^\w]', v))

    if starts_punct or has_garbage:
        return 0.2

    if (has_road or has_intersection) and 10 <= n <= 200:
        return 1.0

    # Has some content but no road terminology
    return 0.6


# ── Accident type plausibility ────────────────────────────────────────

_COLLISION_TERMS = re.compile(
    r'\b(?:collision|crash|impact|rear.?end|head.?on|angle|sideswipe|rollover|'
    r'overturn|fixed.?object|pedestrian|bicycle|chain|reaction|broadside|'
    r'intersection|turning|backing|parking|single.?vehicle|multi.?vehicle|'
    r'same.?direction|opposite.?direction|right.?angle|left.?turn|right.?turn|'
    r'run.?off.?road|hit.?and.?run)\b',
    re.I,
)


def _plausibility_accident_type(value: str) -> float:
    v = value.strip()
    n = len(v)
    if n < 5 or n > 150:
        return 0.2

    if _COLLISION_TERMS.search(v):
        if n <= 80:
            return 1.0
        return 0.7   # long but has vocab

    return 0.6


# ── Contributing factors plausibility ─────────────────────────────────

_CODED_FACTOR_RE = re.compile(r'\[\d{2}\]')

_FACTOR_TERMS = re.compile(
    r'\b(?:speed|alcohol|drug|distract|fatigue|fatigued|asleep|impair|'
    r'vision|obstruct|failure|control|weather|fog|rain|ice|snow|defect|'
    r'follow|signal|right.?of.?way|reckless|aggressive|'
    r'mechanical|brake|tire|glare|animal|pedestrian|'
    r'bicycle|inattentive|inexperienc|unknown|none)',
    re.I,
)


def _plausibility_contributing_factors(value: str) -> float:
    v = value.strip()
    n = len(v)
    if n < 5 or n > 300:
        return 0.2

    # Trailing comma alone → fragment
    if re.match(r'^[^,]+,$', v):
        return 0.3

    has_coded = bool(_CODED_FACTOR_RE.search(v))
    has_vocab = bool(_FACTOR_TERMS.search(v))

    if has_coded or has_vocab:
        return 1.0

    return 0.5


# ── Property damage plausibility ──────────────────────────────────────

_DAMAGE_TERMS = re.compile(
    r'\b(?:damage|damag|crush|crumple|shatter|dent|scratch|deform|bent|'
    r'fracture|deflect|deploy|airbag|bumper|fender|'
    r'windshield|mirror|panel|frame|axle|guardrail|'
    r'median|concrete|lamp|assembly|quarter.?panel|lift.?gate|'
    r'grille|radiator|strut|spindle)\b',
    re.I,
)

_PARENTHESIZED_LABEL_RE = re.compile(r'^\([A-Z\-/\s]+\)$')


def _plausibility_property_damage(value: str) -> float:
    v = value.strip()
    n = len(v)
    if n < 10 or n > 500:
        return 0.2

    # Parenthesized label only → extraction artifact
    if _PARENTHESIZED_LABEL_RE.match(v):
        return 0.2

    if _DAMAGE_TERMS.search(v):
        return 1.0

    return 0.5


# ── EMS agency plausibility ───────────────────────────────────────────

_EMS_TERMS = re.compile(
    r'\b(?:ems|ambulance|paramedic|medic|rescue|fire\s*dept|fire\s*department|'
    r'hospital|medical|health|emergency|emerg|dept|unit|transport|trauma)\b',
    re.I,
)

_NA_RE = re.compile(r'^(?:n/?a|none|not\s+applicable|not\s+required)\s*$', re.I)

_PHONE_RE = re.compile(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b')


def _plausibility_ems_agency(value: str) -> float:
    v = value.strip()
    n = len(v)

    if _NA_RE.match(v):
        return 0.3

    if n < 5 or n > 100:
        return 0.2

    if _PHONE_RE.search(v):
        return 0.2

    if _EMS_TERMS.search(v):
        return 1.0

    # Has some content but no EMS vocabulary
    return 0.5


# ── Registry ──────────────────────────────────────────────────────────

_REGISTRY: dict[str, Callable[[str], float]] = {
    "date_time":              _plausibility_date,
    "report_number":          _plausibility_report_number,
    "vin":                    _plausibility_vin,
    "year":                   _plausibility_year,
    "weather":                _plausibility_weather,
    "light_condition":        _plausibility_light_condition,
    "officer":                _plausibility_person_name,
    "location":               _plausibility_location,
    "accident_type":          _plausibility_accident_type,
    "contributing_factors":   _plausibility_contributing_factors,
    "property_damage":        _plausibility_property_damage,
    "ems_agency":             _plausibility_ems_agency,
}


def plausibility_score(field_id: str, value: str) -> float:
    """Return semantic plausibility in [0.0, 1.0]; 0.5 if field has no registered check."""
    fn = _REGISTRY.get(field_id)
    if fn is None:
        return 0.5
    try:
        result = fn(value)
        return float(max(0.0, min(1.0, result)))
    except Exception:
        return 0.5
