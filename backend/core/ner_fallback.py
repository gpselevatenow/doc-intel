"""
spaCy NER fallback for extraction fields that regex couldn't fill.

Runs after the orchestrator. Any field still 'Unknown' / None / '' gets
a second-pass attempt using named entity recognition on the full document text.
Never overwrites a value that regex already found.

Model: en_core_web_lg — local, MIT license, ~560 MB, ~40 ms per doc on CPU.
Loaded once at first call (module-level singleton).
"""

import re
import spacy

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_lg")
    return _nlp


def _empty(val) -> bool:
    return not val or str(val).strip() in ("", "Unknown", "N/A")


def _entities_by_type(doc) -> dict:
    out = {}
    for ent in doc.ents:
        out.setdefault(ent.label_, []).append(ent.text.strip())
    return out


# ── Field-specific pickers ────────────────────────────────────────────────────

def _pick_date(by_type: dict, text: str) -> str | None:
    """Prefer dates that look like MM/DD/YYYY or month-name format near crash/incident keywords."""
    dates = by_type.get("DATE", [])
    # Prefer explicit numeric date formats
    for d in dates:
        if re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', d):
            return d
    # Prefer month-name dates
    for d in dates:
        if re.search(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}', d, re.IGNORECASE):
            return d
    # Fall back to anything that looks like a date near incident keywords
    ctx = re.search(
        r'(?:date|incident|occurred?|crash|collision)\s*[:\-]?\s*'
        r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        text, re.IGNORECASE
    )
    if ctx:
        return ctx.group(1)
    return dates[0] if dates else None


def _pick_agency(by_type: dict, text: str) -> str | None:
    """ORG entity containing law-enforcement keywords."""
    def _strip_prefix(s: str) -> str:
        # Remove state prefixes like "STATE OF CA - " or "STATE OF CALIFORNIA - "
        s = re.sub(r'^(?:STATE\s+OF\s+\w+\s*[-–]+\s*)+', '', s, flags=re.IGNORECASE).strip()
        return re.sub(r'^(?:the|a)\s+', '', s, flags=re.IGNORECASE)

    for org in by_type.get("ORG", []):
        if re.search(r'police|sheriff|patrol|department|highway|troop|bureau|dpd|lapd|nypd|fhp', org, re.IGNORECASE):
            return _strip_prefix(org)
    # Regex fallback: known department patterns anchored at a word boundary
    m = re.search(
        r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})\s+(?:Police Department|Sheriff\'?s Office|Highway Patrol|Department of Public Safety|Police Dept\.?)',
        text
    )
    if m:
        return _strip_prefix(m.group(0).strip())
    return None


def _pick_officer(by_type: dict, text: str) -> str | None:
    """PERSON entity that appears near officer-related keywords."""
    # Try context-anchored regex first — most reliable
    ctx = re.search(
        r'(?:officer|reporting officer|investigating officer|sgt\.?|lt\.?|cpl\.?|det\.?|deputy|trooper)'
        r'[\s:,]+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)',
        text, re.IGNORECASE
    )
    if ctx:
        return ctx.group(1).strip()
    # Fall back to last PERSON entity — officers usually appear at end of report
    # Require at least two words (first + last name) to avoid labels like "Plate" or "Ford"
    persons = by_type.get("PERSON", [])
    for p in reversed(persons):
        if re.match(r'^[A-Z][a-z]+(?: [A-Z]\.?)? [A-Z][a-z]+', p):
            return p
    return None


def _pick_location(by_type: dict, text: str) -> str | None:
    """Street address regex first; GPE/LOC/FAC entities as fallback."""
    m = re.search(
        r'\d+\s+[A-Za-z0-9 ]+?'
        r'(?:Street|Avenue|Road|Boulevard|Drive|Lane|Court|Way|Place|Highway|Blvd|Ave|St|Rd|Dr|Ln|Ct|Hwy)\b'
        r'[^,\n]{0,40}',
        text, re.IGNORECASE
    )
    if m:
        return m.group(0).strip()
    for label in ("FAC", "LOC", "GPE"):
        locs = by_type.get(label, [])
        if locs:
            return locs[0]
    return None


def _pick_org(by_type: dict, keyword_hint: str = "") -> str | None:
    """Generic ORG picker — optionally filter by keyword hint."""
    for org in by_type.get("ORG", []):
        if not keyword_hint or re.search(keyword_hint, org, re.IGNORECASE):
            return org
    orgs = by_type.get("ORG", [])
    return orgs[0] if orgs else None


def _pick_person(by_type: dict) -> str | None:
    persons = by_type.get("PERSON", [])
    return persons[0] if persons else None


# ── Public API ────────────────────────────────────────────────────────────────

def _apply_learned_patterns(text: str, record: dict) -> dict:
    """
    First-pass: apply regex patterns learned from user corrections.
    Runs before NER so user-validated patterns take priority.
    """
    try:
        from database import get_learned_patterns
    except ImportError:
        return record

    result = dict(record)
    for field, val in result.items():
        if not _empty(val):
            continue
        for pat in get_learned_patterns(field):
            try:
                m = re.search(pat, text)
                if m:
                    candidate = m.group(1).strip()
                    if candidate and len(candidate) >= 2:
                        result[field] = candidate
                        break
            except re.error:
                continue
    return result


def ner_fill_unknowns(text: str, record: dict, doc_type: str = "police") -> dict:
    """
    Fill any Unknown/empty fields in `record` using spaCy NER on `text`.
    `doc_type` is 'police', 'ia', or 'hsmv' — controls which fields are targeted.

    Returns a new dict; original values are never overwritten.
    """
    result = _apply_learned_patterns(text, record)

    nlp = _get_nlp()
    # Limit to first 50 000 chars — covers virtually all docs, respects spaCy token limits
    doc = nlp(text[:50000])
    by_type = _entities_by_type(doc)

    # ── Police / HSMV ──────────────────────────────────────────────────────────
    if doc_type in ("police", "hsmv"):
        if _empty(result.get("date_time")):
            # MMUCC label variants not caught by template regex
            ctx = re.search(
                r'(?:crash\s+date(?:/time)?|date(?:/time)?\s+of\s+crash|date\s+of\s+accident|'
                r'accident\s+date|date\s+of\s+loss|occurred\s+on|date\s+occurred)'
                r'[\s:,\-]+([^\n]{3,40})',
                text, re.IGNORECASE
            )
            if ctx:
                result["date_time"] = ctx.group(1).strip()
            else:
                val = _pick_date(by_type, text)
                if val:
                    result["date_time"] = val

        if _empty(result.get("location")):
            # MMUCC: crash location, place of crash, scene address
            ctx = re.search(
                r'(?:crash\s+location|place\s+of\s+crash|scene\s+(?:location|address)|'
                r'accident\s+(?:location|scene|address)|where\s+did\s+crash\s+occur)'
                r'[\s:,\-]+([^\n]{5,120})',
                text, re.IGNORECASE
            )
            if ctx:
                result["location"] = ctx.group(1).strip()
            else:
                val = _pick_location(by_type, text)
                if val:
                    result["location"] = val

        if _empty(result.get("agency")):
            val = _pick_agency(by_type, text)
            if val:
                result["agency"] = val

        if _empty(result.get("officer")):
            # MMUCC: rank and name, officer id
            ctx = re.search(
                r'(?:rank\s+(?:and|&)\s+name|rank\s*/\s*name|officer\s+rank)'
                r'[\s:,\-]+([A-Za-z][A-Za-z\s.]+)',
                text, re.IGNORECASE
            )
            if ctx:
                result["officer"] = ctx.group(1).strip()
            else:
                val = _pick_officer(by_type, text)
                if val:
                    result["officer"] = val

        if _empty(result.get("report_number")):
            ctx = re.search(
                r'(?:crash\s+report\s+(?:number|no\.?)|hsmv\s+crash\s+report\s+(?:number|no\.?)|'
                r'agency\s+report\s+(?:number|no\.?)|case|report|complaint|cad|ccn)'
                r'\s*(?:number|no\.?|#)?\s*[:\-]?\s*([A-Za-z0-9\-/#]{4,25})',
                text, re.IGNORECASE
            )
            if ctx:
                result["report_number"] = ctx.group(1).strip()

        if _empty(result.get("weather")):
            # Keyword scan for weather near relevant context
            ctx = re.search(
                r'(?:weather|atmospheric|road\s+conditions?)[\s:,\-]+'
                r'(?P<val>clear|sunny|rain(?:ing)?|snow(?:ing)?|fog(?:gy)?|overcast|'
                r'icy|ice|cloudy|hail|sleet|wet|dry|mist(?:y)?|partly\s+cloudy)',
                text, re.IGNORECASE
            )
            if ctx:
                result["weather"] = ctx.group("val").strip()

        if _empty(result.get("contributing_factors")):
            ctx = re.search(
                r'(?:contributing\s+factors?|primary\s+contributing|driver\s+action|'
                r'human\s+(?:contributing\s+)?factor|vehicle\s+factor)'
                r'[\s:,\-]+([^\n]{3,120})',
                text, re.IGNORECASE
            )
            if ctx:
                result["contributing_factors"] = ctx.group(1).strip()

        if _empty(result.get("property_damage")):
            ctx = re.search(
                r'(?:property\s+damage|property\s+damaged|estimated\s+damage|damage\s+description)'
                r'[\s:,\-]+([^\n]{3,120})',
                text, re.IGNORECASE
            )
            if ctx:
                result["property_damage"] = ctx.group(1).strip()

        if _empty(result.get("accident_type")):
            # Infer from MMUCC first harmful event or manner of collision in narrative
            ctx = re.search(
                r'(?:manner\s+of\s+collision|first\s+harmful\s+event|type\s+of\s+(?:crash|accident|collision))'
                r'[\s:,\-]+([^\n]{3,80})',
                text, re.IGNORECASE
            )
            if ctx:
                result["accident_type"] = ctx.group(1).strip()

    # ── IA Report ──────────────────────────────────────────────────────────────
    if doc_type == "ia":
        if _empty(result.get("inspection_date")):
            # IA-specific date labels
            ctx = re.search(
                r'(?:date\s+of\s+inspection|inspection\s+date|date\s+inspected|'
                r'field\s+inspection\s+date|date\s+loss\s+examined|date\s+of\s+survey)'
                r'[\s:,\-]+([^\n]{3,40})',
                text, re.IGNORECASE
            )
            if ctx:
                result["inspection_date"] = ctx.group(1).strip()
            else:
                val = _pick_date(by_type, text)
                if val:
                    result["inspection_date"] = val

        if _empty(result.get("inspection_firm")):
            # Try org entities with adjuster/claims keyword hint
            val = _pick_org(by_type, keyword_hint=r'adjuster|claims|inspection|services|group|associates|consulting|insurance')
            if val:
                result["inspection_firm"] = val

        if _empty(result.get("cause_of_loss")):
            ctx = re.search(
                r'(?:cause\s+of\s+(?:loss|damage|claim)|peril|origin\s+of\s+loss|'
                r'type\s+of\s+(?:loss|peril)|loss\s+type|loss\s+description)'
                r'[\s:,\-]+([^\n]{3,80})',
                text, re.IGNORECASE
            )
            if ctx:
                result["cause_of_loss"] = ctx.group(1).strip()

        if _empty(result.get("settlement")):
            ctx = re.search(
                r'(?:recommended\s+settlement|loss\s+reserve|current\s+reserve|'
                r'total\s+(?:settlement|claim|indemnity|award)|settlement\s+(?:amount|value))'
                r'[\s:,\-]*\$?([\d,\.]+)',
                text, re.IGNORECASE
            )
            if ctx:
                result["settlement"] = "$" + ctx.group(1).strip()

        if _empty(result.get("subrogation")):
            ctx = re.search(
                r'(?:subrogation\s+(?:potential|opportunity|rights?)|recovery\s+opportunity|'
                r'third\s+party\s+(?:recovery|liability))'
                r'[\s:,\-]+([^\n]{2,60})',
                text, re.IGNORECASE
            )
            if ctx:
                result["subrogation"] = ctx.group(1).strip()

    return result
