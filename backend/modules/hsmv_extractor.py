"""
Custom extractor for Florida HSMV 90010S Traffic Crash Report.

Docling renders this form with labels scattered across pages and actual filled
values clustered near page footers. This extractor uses those footers as
positional anchors.

Key anchors:
  HSMV 90010 S (E)   - end of crash-identifier page; crash location is 1 line before,
                        witnesses are 2-4 lines before, date/case# come from DATE OF REPORT cluster.
  HSMV 90010 S (V/P) - end of vehicle/person page; owner/color/YMM/plate are the 4 lines before.
"""

import re

_MAKES = sorted([
    'ACURA', 'ALFA', 'AUDI', 'BMW', 'BUICK', 'CADILLAC', 'CHEVROLET', 'CHEVY',
    'CHRYSLER', 'DODGE', 'FERRARI', 'FORD', 'GENESIS', 'GMC', 'HARLEY',
    'HONDA', 'HYUNDAI', 'INFINITI', 'JAGUAR', 'JEEP', 'KIA', 'KAWASAKI',
    'LANDROVER', 'LAND', 'LEXUS', 'LINCOLN', 'LUCID', 'MASERATI', 'MAZDA',
    'MERCEDES', 'MINI', 'MITSUBISHI', 'NISSAN', 'PONTIAC', 'PORSCHE', 'RAM',
    'RIVIAN', 'SATURN', 'SUBARU', 'SUZUKI', 'TESLA', 'TOYOTA', 'VOLKSWAGEN',
    'VOLVO', 'VW', 'YAMAHA',
], key=len, reverse=True)


def _strip_headings(text):
    return '\n'.join(re.sub(r'^#{1,6}\s+', '', ln) for ln in text.split('\n'))


def _ne(text):
    """Non-empty lines as list of (line_index, stripped_content)."""
    return [(i, ln.strip()) for i, ln in enumerate(text.split('\n')) if ln.strip()]


def _find(ne, pattern, after=0):
    """Index into ne where pattern matches, at or after position `after`."""
    for idx, (_, ln) in enumerate(ne):
        if idx >= after and re.search(pattern, ln, re.IGNORECASE):
            return idx
    return None


def _val(ne, anchor, offset):
    """Content of ne[anchor + offset], or None."""
    t = anchor + offset
    return ne[t][1] if 0 <= t < len(ne) else None


def _split_datetime(raw):
    """'05/12/202614:30' → ('05/12/2026', '14:30')."""
    m = re.match(r'(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})', raw)
    return (m.group(1), m.group(2)) if m else (raw, '')


def _split_ymm(raw):
    """'2020TOYOTACAMRY' → ('2020', 'Toyota', 'Camry')."""
    if not re.match(r'^\d{4}[A-Za-z]', raw):
        return '', '', raw
    year = raw[:4]
    rest = raw[4:].upper()
    for make in _MAKES:
        if rest.startswith(make):
            model = rest[len(make):].title() or 'Unknown'
            return year, make.title(), model
    # fallback: split on capitalisation boundary
    parts = re.findall(r'[A-Z][a-z]*', raw[4:].title())
    return year, (parts[0] if parts else 'Unknown'), (' '.join(parts[1:]) if len(parts) > 1 else 'Unknown')


def _parse_owner(line):
    """'JOHN DOE 456 ELM ST MIAMI FL 33101' → ('John Doe', '456 ELM ST MIAMI FL 33101')."""
    m = re.match(r'^([A-Z][A-Z\s]+?)\s+(\d+\s+.+)$', line)
    if m:
        return m.group(1).strip().title(), m.group(2).strip()
    return line.title(), 'Unknown'


def _is_witness(line):
    """Witness lines: long, mixed-case, internally spaced, not a form label/footer."""
    return (
        len(line) > 25
        and '  ' in line
        and not re.match(r'^[A-Z\s&;#]+$', line)
        and not re.match(r'^\d', line)
        and not re.search(r'HSMV|Page \\_|rev \d', line, re.IGNORECASE)
    )


def _blank_vehicle():
    return {
        'vin': 'Unknown', 'plate': 'Unknown', 'make': 'Unknown',
        'year': 'Unknown', 'model': 'Unknown', 'color': 'Unknown',
        'damages': 'Unknown', 'owner_name': 'Unknown', 'owner_address': 'Unknown',
        'insurance_company': 'Unknown', 'policy_number': 'Unknown',
        'towed': 'Unknown', 'towing_company': 'Unknown',
    }


def extract_hsmv_report(markdown_text: str) -> dict:
    text = _strip_headings(markdown_text)
    ne = _ne(text)

    result = {
        'date_time': 'Unknown', 'location': 'Unknown', 'weather': 'Unknown',
        'accident_type': 'Unknown', 'agency': 'Unknown', 'officer': 'Unknown',
        'report_number': 'Unknown', 'ems_agency': 'Unknown',
        'vehicles': [], 'parties': [], 'witnesses': [],
    }

    # ── PAGE (E) CLUSTER ─────────────────────────────────────────────────────
    # Anchored by: HSMV 90010 S (E) page footer
    # Cluster before footer: crash_location(-1), witnesses(-2..-4)
    # DATE OF REPORT cluster: date+time(+1), case_number(+2)
    e_footer = _find(ne, r'HSMV 90010 S \(E\)')
    dt_anchor = _find(ne, r'^DATE OF REPORT$')

    if dt_anchor is not None:
        raw_dt = _val(ne, dt_anchor, 1)
        if raw_dt:
            date_str, time_str = _split_datetime(raw_dt)
            result['date_time'] = f"{date_str} {time_str}".strip()

        case_val = _val(ne, dt_anchor, 2)
        if case_val and re.match(r'^[\w\-]{4,}$', case_val):
            result['report_number'] = case_val

    if e_footer is not None and e_footer > 0:
        loc = _val(ne, e_footer, -1)
        if loc and not re.search(r'HSMV|Page|\\_', loc):
            result['location'] = loc

        witnesses = []
        for off in range(-4, -1):
            ln = _val(ne, e_footer, off)
            if ln and _is_witness(ln):
                parts = re.split(r'\s{3,}', ln)
                witnesses.append({
                    'name': parts[0].strip().title() if parts else 'Unknown',
                    'dob': 'Unknown',
                    'address': parts[1].strip() if len(parts) > 1 else 'Unknown',
                    'phone': 'Unknown',
                    'statement': 'Unknown',
                })
        result['witnesses'] = witnesses

    # ── PAGE (V/P) VEHICLE CLUSTER ───────────────────────────────────────────
    # 4 non-empty lines before the V/P footer: plate(-4), YMM(-3), color(-2), owner(-1)
    vehicles = []
    vp_search_start = 0
    while True:
        vp_footer = _find(ne, r'HSMV 90010 S \(V/P\)', after=vp_search_start)
        if vp_footer is None:
            break

        owner_raw = _val(ne, vp_footer, -1)
        color     = _val(ne, vp_footer, -2)
        ymm_raw   = _val(ne, vp_footer, -3)
        plate     = _val(ne, vp_footer, -4)

        year = make = model = 'Unknown'
        if ymm_raw and re.match(r'^\d{4}', ymm_raw):
            year, make, model = _split_ymm(ymm_raw)

        if not color or not re.match(r'^[A-Za-z]{2,15}$', color):
            color = 'Unknown'

        # Reject if plate looks like a form label rather than an actual plate
        if not plate or len(plate) > 15 or re.match(r'^(STATE|TRAILER|REGISTRATION|SOURCE|NAME|DATE)', plate, re.IGNORECASE):
            plate = 'Unknown'

        owner_name, owner_addr = 'Unknown', 'Unknown'
        if owner_raw and not re.match(r'^(HSMV|Page)', owner_raw, re.IGNORECASE):
            owner_name, owner_addr = _parse_owner(owner_raw)

        # Skip clusters with no real vehicle data (spurious V/P footer matches on person pages)
        if year == 'Unknown' and make == 'Unknown' and plate == 'Unknown':
            vp_search_start = vp_footer + 1
            continue

        v = _blank_vehicle()
        v.update({
            'plate': plate or 'Unknown',
            'year': year, 'make': make, 'model': model,
            'color': color.title() if color != 'Unknown' else 'Unknown',
            'owner_name': owner_name, 'owner_address': owner_addr,
        })
        vehicles.append(v)
        vp_search_start = vp_footer + 1

    # VIN: 17-char alphanumeric (standard VIN format)
    for _, ln in ne:
        if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', ln):
            if vehicles:
                vehicles[0]['vin'] = ln
            break

    result['vehicles'] = vehicles

    # ── PERSON SECTIONS ──────────────────────────────────────────────────────
    # On each V/P page: "REPORTING AGENCY CASE NUMBER" then "HSMV CRASH REPORT NUMBER"
    # then the person's name (2 lines later). DL# matches ^[A-Z]\d{5,}$.
    parties = []
    person_search_start = 0
    first_vp = _find(ne, r'HSMV 90010 S \(V/P\)')
    if first_vp is not None:
        while True:
            racs = _find(ne, r'^REPORTING AGENCY CASE NUMBER$', after=person_search_start)
            if racs is None:
                break
            # Only look at RACS labels that are on V/P pages (after first V/P footer)
            if racs < first_vp:
                person_search_start = racs + 1
                continue

            name_raw = _val(ne, racs, 2)
            if name_raw and re.match(r'^[A-Z][A-Z\s]{2,}$', name_raw):
                dl_idx = _find(ne, r'^[A-Z]\d{5,}$', after=racs)
                dl = ne[dl_idx][1] if dl_idx is not None else 'Unknown'

                dob_idx = _find(ne, r'^\d{2}/\d{2}/\d{4}$', after=racs)
                dob = ne[dob_idx][1] if dob_idx is not None else 'Unknown'

                parties.append({
                    'role': 'Driver',
                    'name': name_raw.title(),
                    'dob': dob,
                    'address': 'Unknown',
                    'license_number': dl,
                    'condition': 'Unknown',
                    'injuries': 'Unknown',
                    'substance_involvement': 'None reported',
                    'transported': False,
                    'transported_to': 'Unknown',
                    'citations': 'None',
                    'citations_list': [],
                })

            person_search_start = racs + 1

    result['parties'] = parties

    # ── AGENCY ───────────────────────────────────────────────────────────────
    agency_m = re.search(
        r'(?P<value>[A-Za-z ]+(?:Police Department|Sheriff\'?s Office|Highway Patrol|Department of Public Safety))',
        text, re.IGNORECASE
    )
    if agency_m:
        result['agency'] = agency_m.group('value').strip()

    return result
