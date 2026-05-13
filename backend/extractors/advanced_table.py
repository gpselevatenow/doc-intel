import json
import re
from typing import Any
from pydantic import BaseModel

from core.candidate import Candidate
from core.document_model import Document
from extractors.base import Strategy, register

class AdvancedTableConfig(BaseModel):
    table_type: str  # "vehicles", "parties", "witnesses"

@register("advanced_table")
class AdvancedTableStrategy(Strategy):
    """
    Extracts complex tables (Vehicles, Parties, Witnesses) from markdown using highly robust multi-pass logic.
    """
    def run(self, document: Document, field_id: str, config: dict) -> list[Candidate]:
        cfg = AdvancedTableConfig.model_validate(config)
        text = document.markdown or ""
        if not text:
            return []

        result_list = []

        def has_word(s: str, w: str) -> bool:
            return re.search(rf'\b{re.escape(w)}\b', s.lower()) is not None

        if cfg.table_type == "vehicles":
            aliases = {
                "vin": ["vin", "vehicle identification", "identification number"],
                "plate": ["plate", "license plate", "tag"],
                "year_make_model": ["year / make / model", "year/make/model", "make/model/year", "yr/make/model"],
                "make": ["make", "manufacturer"],
                "year": ["year", "yr"],
                "model": ["model", "mod"],
                "color": ["color", "colour", "vehicle color"],
                "damages": ["damage", "damages", "severity"],
                "owner_name": ["owner name", "owner"],
                "owner_address": ["owner address", "owner addr", "owner street"],
                "insurance_company": ["insurance", "insurance company", "carrier"],
                "policy_number": ["policy", "policy number", "policy no"],
                "towed": ["towed", "tow"],
                "towing_company": ["towing company", "towed by", "tower"],
            }
            vehicles_dict = {}
            lines = text.splitlines()
            current_entity = {}
            current_id = None
            auto_counter = 0

            def save_vehicle():
                nonlocal current_entity, current_id
                if current_id and current_entity:
                    if current_id not in vehicles_dict:
                        vehicles_dict[current_id] = {
                            "vin": "Unknown", "plate": "Unknown", "make": "Unknown",
                            "year": "Unknown", "model": "Unknown", "color": "Unknown",
                            "damages": "Unknown", "owner_name": "Unknown",
                            "owner_address": "Unknown", "insurance_company": "Unknown",
                            "policy_number": "Unknown", "towed": "Unknown",
                            "towing_company": "Unknown"
                        }
                    for k, v in current_entity.items():
                        if k != "_id":
                            vehicles_dict[current_id][k] = v

            for line in lines:
                line = line.strip()
                # Strip pdfplumber CID character artifacts before parsing
                line = re.sub(r'\(cid:\d+\)', '', line).strip()
                if not line:
                    continue

                # Match vehicle section headers:
                #   "B. UNIT / VEHICLE #1 (COMMERCIAL)"  -- multi-column crash report format
                #   "Vehicle 1:", "Unit 2:", "V1:"        -- simple formats
                #   "#: V1"                               -- table header format
                v_match = re.search(
                    r'(?i)(?:^|\b)(?:'
                    r'#\s*:\s*V(\d+)'                                       # group 1: "#: V1"
                    r'|UNIT\s*/\s*VEH\S*\s*#?\s*(\d+)'                    # group 2: "UNIT / VEHICLE #1" (VEH\S* tolerates OCR artifacts like VEHICLAE)
                    r'|(?:Vehicle|Unit|Veh\.?)\s*[#]?\s*(\d+)\s*[:\s]'    # group 3: "Vehicle 1:", "Unit 2:"
                    r'|V(\d+)\s*[:]\s*'                                    # group 4: "V1:"
                    r')',
                    line
                )
                # Allow "UNIT / VEHICLE #N" even when prefixed by section letter ("B. ").
                # Reject mid-line bare "Unit N" matches (e.g. "EMS - Unit 14").
                if v_match:
                    is_unit_vehicle_header = v_match.group(2) is not None
                    if not is_unit_vehicle_header and v_match.group(3) is not None and v_match.start() > 0:
                        if re.match(r'(?i)unit', v_match.group(0)) and line[:v_match.start()].strip():
                            v_match = None

                # Match: VEHICLE - STOLEN / INVOLVED, VEHICLE - RECOVERED, etc. (crime/theft reports)
                stolen_match = (not v_match) and bool(re.match(
                    r'(?i)VEHICLE\s*[-–/]+\s*(?:STOLEN|INVOLVED|RECOVERED|REPORTED)',
                    line
                ))
                if v_match:
                    save_vehicle()
                    num = v_match.group(1) or v_match.group(2) or v_match.group(3) or v_match.group(4)
                    current_id = f"V{num}" if num else v_match.group(0).strip()
                    current_entity = {}
                    # Parse inline attributes from rest of line (only for non-"UNIT / VEHICLE" headers)
                    if not v_match.group(2):
                        rest = line[v_match.end():].strip()
                        if rest:
                            # CHP format: "VEHICLE 1 2022 Tesla Model S (Gray)" — YYYY MAKE MODEL (COLOR)
                            ymm_inline = re.match(
                                r'^(\d{4})\s+([A-Za-z][A-Za-z0-9\-]+)\s+(.+?)(?:\s*\(([^)]+)\))?\s*$',
                                rest
                            )
                            if ymm_inline and not ':' in rest and not '|' in rest:
                                current_entity.setdefault("year", ymm_inline.group(1))
                                current_entity.setdefault("make", ymm_inline.group(2))
                                model_part = ymm_inline.group(3).strip()
                                current_entity.setdefault("model", model_part)
                                if ymm_inline.group(4):
                                    current_entity.setdefault("color", ymm_inline.group(4).strip())
                            else:
                                segs = [s.strip() for s in rest.split('|') if s.strip()] if '|' in rest else [rest]
                                for seg in segs:
                                    if ':' in seg:
                                        k, v = seg.split(':', 1)
                                        k, v = k.strip().lower(), v.strip()
                                    else:
                                        words = seg.split(None, 1)
                                        k, v = (words[0].strip().lower(), words[1].strip()) if len(words) == 2 else ('', '')
                                    if not k or not v:
                                        continue
                                    for target_key, alias_list in aliases.items():
                                        if any(has_word(k, a) or a in k for a in alias_list):
                                            if target_key == "year_make_model":
                                                ymm = re.match(r'(\d{4})\s+(\S+)\s+(.+)', v)
                                                if ymm:
                                                    current_entity.setdefault("year", ymm.group(1))
                                                    current_entity.setdefault("make", ymm.group(2))
                                                    current_entity.setdefault("model", ymm.group(3).strip())
                                            else:
                                                current_entity[target_key] = v
                                            break
                    continue
                elif stolen_match:
                    save_vehicle()
                    auto_counter += 1
                    current_id = f"V{auto_counter}"
                    current_entity = {}
                    continue

                if current_id is None:
                    continue

                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()

                    for target_key, alias_list in aliases.items():
                        if any(has_word(key, a) or a in key for a in alias_list):
                            if target_key == "year_make_model":
                                ymm = re.match(r'(\d{4})\s+(\S+)\s+(.+)', val)
                                if ymm:
                                    current_entity.setdefault("year", ymm.group(1))
                                    current_entity.setdefault("make", ymm.group(2))
                                    current_entity.setdefault("model", ymm.group(3).strip())
                            elif target_key == "owner_name" and re.search(
                                r'same as (?:driver|operator)', val, re.IGNORECASE
                            ):
                                current_entity[target_key] = val
                                current_entity["_owner_same_as_driver"] = True
                            else:
                                current_entity[target_key] = val
                            break
                else:
                    # Compound inline line with no colon — parse keyword-anchored vehicle fields
                    # "Year 2025 Make Volvo Trucks Model VHD" or "YYYY MAKE MODEL (COLOR)"
                    # Strip pdfplumber CID artifacts and trailing single-letter column artifacts first
                    clean_line = re.sub(r'\(cid:\d+\)', '', line).strip()

                    m = re.search(r'(?i)\bYear\s+(\d{4})\b', clean_line)
                    if m:
                        current_entity.setdefault("year", m.group(1))

                    m = re.search(r'(?i)\bMake\s+(.+?)(?=\s+Model\s+|\s+Color\s+|\s+VIN\b|\s*$)', clean_line)
                    if m:
                        val = re.sub(r'\s+U$', '', m.group(1)).strip()
                        current_entity.setdefault("make", val)

                    m = re.search(r'(?i)\bModel\s+(.+?)(?=\s+Color\s+|\s+VIN\b|\s+Year\s+|\s*$)', clean_line)
                    if m:
                        val = re.sub(r'\s+U$', '', m.group(1)).strip()
                        current_entity.setdefault("model", val)

                    m = re.search(r'(?i)\bColor\s+([A-Za-z][A-Za-z\s]+?)(?=\s+License|\s+Plate|\s+VIN\b|\s*$)', clean_line)
                    if m:
                        current_entity.setdefault("color", m.group(1).strip())

                    m = re.search(r'(?i)\bVIN\s+([A-HJ-NPR-Z0-9]{17})\b', clean_line)
                    if m:
                        current_entity.setdefault("vin", m.group(1))

                    m = re.search(r'(?i)(?:License\s+Plate|Plate)\s+([A-Z0-9]{3,8})\b', clean_line)
                    if m:
                        current_entity.setdefault("plate", m.group(1))

                    # "YYYY MAKE MODEL (COLOR)" bare line
                    ymm_bare = re.match(
                        r'^(\d{4})\s+([A-Za-z][A-Za-z0-9\-]+)\s+(.+?)(?:\s*\(([^)]+)\))?\s*$',
                        clean_line
                    )
                    if ymm_bare and not re.search(r'(?i)(Driver|Owner|Insurance|Policy|DL|Restraint|Injury)', clean_line):
                        current_entity.setdefault("year", ymm_bare.group(1))
                        current_entity.setdefault("make", ymm_bare.group(2))
                        model_val = re.sub(r'\s+U$', '', ymm_bare.group(3)).strip()
                        current_entity.setdefault("model", model_val)
                        if ymm_bare.group(4):
                            current_entity.setdefault("color", ymm_bare.group(4).strip())

            save_vehicle()

            # Fallback: theft/incident reports have no V1/V2 delimiter — single vehicle fields appear bare
            if not vehicles_dict and any(k in current_entity for k in ("vin", "plate", "make", "model", "year")):
                vehicles_dict["V1"] = {
                    "vin": "Unknown", "plate": "Unknown", "make": "Unknown",
                    "year": "Unknown", "model": "Unknown", "color": "Unknown",
                    "damages": "Unknown", "owner_name": "Unknown",
                    "owner_address": "Unknown", "insurance_company": "Unknown",
                    "policy_number": "Unknown", "towed": "Unknown",
                    "towing_company": "Unknown"
                }
                for k, v in current_entity.items():
                    if k in vehicles_dict["V1"]:
                        vehicles_dict["V1"][k] = v

            result_list = list(vehicles_dict.values())

        elif cfg.table_type == "parties":
            parties = []
            current_entity = {}
            lines = text.splitlines()

            def save_party():
                nonlocal current_entity
                if not current_entity:
                    return
                # Skip placeholder parties that have only a role and no identifying info
                if not any(current_entity.get(k) for k in ("name", "dob", "address", "license_number", "condition")):
                    return

                condition_raw = current_entity.get("condition", "Unknown")

                # Split injuries from substance involvement
                substance_pattern = r'(?i)(alcohol|drug|intoxicat|dui|dwi|impair|under the influence|substance|narcotics?|cannabis|marijuana)'
                substance_match = re.search(substance_pattern, condition_raw)
                if substance_match:
                    substance = substance_match.group(0)
                    injuries = re.sub(substance_pattern, '', condition_raw, flags=re.IGNORECASE).strip(' ,;')
                else:
                    substance = "None reported"
                    injuries = condition_raw

                # Normalize citations to list
                raw_citations = current_entity.get("citations", "")
                if raw_citations and raw_citations.lower() not in ("none", "unknown", ""):
                    citations_list = [c.strip() for c in re.split(r'[,;|]', raw_citations) if c.strip()]
                else:
                    citations_list = []

                # Transported flag + destination
                transported_to = current_entity.get("transported_to", "Unknown")
                transported = (
                    transported_to not in ("Unknown", "None", "", "N/A")
                    or bool(current_entity.get("_transported_flag"))
                )

                citations_str = ", ".join(citations_list) if citations_list else "None"
                condition_combined = injuries if substance == "None reported" else f"{injuries}; {substance}"

                parties.append({
                    "role": current_entity.get("role", "Unknown"),
                    "name": current_entity.get("name", "Unknown"),
                    "dob": current_entity.get("dob", "Unknown"),
                    "address": current_entity.get("address", "Unknown"),
                    "phone": current_entity.get("phone", "Unknown"),
                    "license_number": current_entity.get("license_number", "Unknown"),
                    "condition": condition_combined,
                    "injuries": injuries if injuries else "None reported",
                    "substance_involvement": substance,
                    "transported": transported,
                    "transported_to": transported_to,
                    "citations": citations_str,
                    "citations_list": citations_list
                })

            delimiter_found = False
            for line in lines:
                line = line.strip()
                # Strip pdfplumber CID character artifacts before parsing
                line = re.sub(r'\(cid:\d+\)', '', line).strip()
                if not line:
                    continue

                # "Driver Information" section header — new Operator party, no inline name to parse
                if re.match(r'(?i)^Driver\s+Information\b', line):
                    save_party()
                    current_entity = {"role": "Operator"}
                    delimiter_found = True
                    continue

                # Match: Party:, Party 1:, PARTY:, Operator:, Driver:, Passenger:, Veh: V1, Person 1:
                # Also: DRIVER 1 (V1) LAST, FIRST (CHP format — no colon, inline name)
                # Also: VICTIM / COMPLAINANT, SUSPECT / OFFENDER (theft/incident reports)
                # MMUCC: OPERATOR (used by NY MV-104, TX CR-2, WA WSP-3000)
                # Driver requires digit / vehicle-ref / colon — prevents narrative "Driver of Unit..." from firing
                party_match = re.match(
                    r'(?i)(Party\s*[#]?\s*\d*\s*:?|Person\s*[#]?\s*\d+\s*:?|Veh\s*:\s*V\d+|Operator\s*[#]?\s*\d*\s*(?:\(V\d+\))?\s*:?|Driver(?!\s+(?:Name|Information)\b)(?=[#\s]*\d|[#\s]*\(V|[#\s]*:)|Passenger\s*[#]?\s*\d*\s*(?:\(V\d+\))?\s*:?|Pedestrian\s*[#]?\s*\d*\s*:?|Bicyclist\s*[#]?\s*\d*\s*:?|VICTIM[\s/]*COMPLAINANT|VICTIM|COMPLAINANT|SUSPECT[\s/]*OFFENDER|SUSPECT|OFFENDER)',
                    line
                )
                if party_match:
                    save_party()
                    current_entity = {}
                    delimiter_found = True
                    full_line_lower = line.lower()
                    if "victim" in full_line_lower or "complainant" in full_line_lower:
                        current_entity["role"] = "Victim"
                    elif "suspect" in full_line_lower or "offender" in full_line_lower:
                        current_entity["role"] = "Suspect"
                    elif "pedestrian" in full_line_lower:
                        current_entity["role"] = "Pedestrian"
                    elif "bicyclist" in full_line_lower or "cyclist" in full_line_lower:
                        current_entity["role"] = "Bicyclist"
                    elif "driver" in full_line_lower or "operator" in full_line_lower:
                        current_entity["role"] = "Operator"
                    elif "passenger" in full_line_lower:
                        current_entity["role"] = "Passenger"
                    elif full_line_lower.startswith("veh"):
                        current_entity["role"] = "Passenger"
                    # Extract inline name (and optional DOB) after delimiter
                    # CHP format: "DRIVER 1 (V1) Jameson, Robert (DOB: 04/12/1985)"
                    rest = line[party_match.end():].strip().rstrip(':').strip()
                    if rest and not rest.startswith('|'):
                        # Match NAME optionally followed by (DOB: ...) — DOB may be truncated
                        name_dob = re.match(
                            r'^([A-Za-z][A-Za-z\s,.\'-]{1,}?)(?:\s*\(DOB:\s*([^)]*)\))?\s*$',
                            rest
                        )
                        if name_dob:
                            name_part = name_dob.group(1).strip().rstrip(',')
                            if name_part:
                                current_entity["name"] = name_part
                            if name_dob.group(2) and name_dob.group(2).strip():
                                current_entity["dob"] = name_dob.group(2).strip()
                        elif re.match(r'^[A-Za-z][A-Za-z\s,.\'-]{2,}', rest):
                            # Truncated: "Chang, Elena (DOB:" — extract name before open paren
                            name_part = re.sub(r'\s*\(.*$', '', rest).strip().rstrip(',')
                            if name_part:
                                current_entity["name"] = name_part
                    continue

                if not delimiter_found:
                    continue

                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()

                    if key in ("role", "party role", "party type", "person type"):
                        current_entity["role"] = val
                    elif any(k in key for k in ("name", "full name", "last name", "person name")):
                        current_entity["name"] = val
                    elif any(k in key for k in ("dob", "date of birth", "birth date", "d.o.b")):
                        dob_clean = val.strip().strip('-').strip()
                        if dob_clean:
                            current_entity["dob"] = dob_clean
                    elif any(k in key for k in ("address", "addr", "street address", "home address", "residence")):
                        current_entity["address"] = val
                    elif any(k in key for k in ("license", "dl #", "dl#", "driver lic", "driver's lic",
                                                 "license number", "license no", "dl number", "lic #")):
                        current_entity["license_number"] = val
                    elif any(k in key for k in ("injury severity", "injury class", "injury status",
                                                 "injury", "condition", "physical condition")):
                        current_entity["condition"] = val
                    elif any(k in key for k in ("alcohol", "drug", "substance", "dui", "dwi",
                                                 "impairment", "bac", "intox")):
                        current_entity["condition"] = (current_entity.get("condition", "") + " " + val).strip()
                    elif any(k in key for k in ("phone", "tel", "cell", "mobile", "contact number")):
                        current_entity["phone"] = val
                    elif any(k in key for k in ("transport", "taken to", "hospital", "medic", "ems unit",
                                                 "transported to", "destination")):
                        current_entity["transported_to"] = val
                        current_entity["_transported_flag"] = True
                    elif any(k in key for k in ("citation", "charge", "infraction", "violation",
                                                 "statute", "ticket")):
                        existing = current_entity.get("citations", "")
                        current_entity["citations"] = (existing + ", " + val).strip(", ") if existing else val
                    elif any(k in key for k in ("physical description", "physical desc",
                                                 "safety equipment", "restraint", "airbag")):
                        current_entity["condition"] = (current_entity.get("condition", "") + " " + val).strip()
                    elif any(k in key for k in ("sex", "gender")):
                        pass
                    elif any(k in key for k in ("license state", "state of license", "dl state")):
                        pass
                    elif "pedestrian" in key:
                        current_entity["role"] = "Pedestrian"
                    elif "passenger" in key:
                        current_entity["role"] = "Passenger"
                    elif "operator" in key or "driver" in key:
                        current_entity["role"] = "Operator"
                else:
                    # Compound inline lines — parse keyword-anchored driver fields
                    # e.g. "Driver Name John Smith DOB 04/16/1982 Age / Sex 44 / M"
                    # e.g. "Address 123 Main St City/State/Zip Houston, TX 12345 Phone (555) 123-4567"
                    # e.g. "DL # TX12345678 DL State TX DL Class Class D"
                    # e.g. "Injury Severity No Apparent Injury Taken To N/A EMS Run # N/A"

                    m = re.search(r'(?i)\bDriver\s+Name\s+(.+?)(?=\s+DOB[A-Z]?[\s\d]|\s+Age\s*[/|]\s*Sex|\s+DL\s+#|\s*$)', line)
                    if m and 'name' not in current_entity:
                        current_entity['name'] = m.group(1).strip()

                    m = re.search(r'(?i)\bDOB[A-Z]?\s*(\d{1,2}/\d{1,2}/\d{2,4})', line)
                    if m:
                        current_entity.setdefault('dob', m.group(1).strip())

                    m = re.search(r'(?i)\bAddress\s+(.+?)(?=\s+City/State/Zip|\s+Phone\s*\(|\s+DL\s+#|\s*$)', line)
                    if m:
                        current_entity.setdefault('address', m.group(1).strip())

                    m = re.search(r'(?i)\bCity/State/Zip\s+(.+?)(?=\s+Phone\s*\(|\s+DL\s+#|\s*$)', line)
                    if m:
                        csz = m.group(1).strip()
                        addr = current_entity.get('address', '')
                        current_entity['address'] = f"{addr}, {csz}".strip(', ') if addr else csz

                    m = re.search(r'(?i)\bPhone\s+(\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4})', line)
                    if m:
                        current_entity.setdefault('phone', m.group(1).strip())

                    m = re.search(r'(?i)\bDL\s*#\s+([A-Z0-9][A-Z0-9\-]{3,20})\b', line)
                    if m:
                        current_entity.setdefault('license_number', m.group(1).strip())

                    m = re.search(r'(?i)\bInjury\s+Severity\s+(.+?)(?=\s+Taken\s+To|\s+EMS\s+Run\s+#|\s*$)', line)
                    if m:
                        sev = m.group(1).strip()
                        current_entity.setdefault('condition', sev)

                    m = re.search(r'(?i)\bTaken\s+To\s+(.+?)(?=\s+EMS\s+Run\s+#|\s*$)', line)
                    if m:
                        dest = m.group(1).strip()
                        current_entity.setdefault('transported_to', dest)
                        if dest.upper() not in ('N/A', 'NONE', 'UNKNOWN', ''):
                            current_entity['_transported_flag'] = True

            save_party()
            result_list = parties

        elif cfg.table_type == "witnesses":
            witnesses = []
            current_entity = {}
            lines = text.splitlines()
            in_witness_section = False
            witness_table_mode = False   # True once we've seen the column header

            def save_witness():
                nonlocal current_entity
                if current_entity:
                    witnesses.append({
                        "name": current_entity.get("name", "Unknown"),
                        "dob": current_entity.get("dob", "Unknown"),
                        "address": current_entity.get("address", "Unknown"),
                        "phone": current_entity.get("phone", "Unknown"),
                        "statement": current_entity.get("statement", "Unknown")
                    })
                    current_entity = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect witness section header
                if re.search(r'(?i)(?:WITNESSES?\s*(?:&|AND)\s*OFFICER|^WITNESSES?$)', line):
                    in_witness_section = True
                    witness_table_mode = False
                    continue

                # Detect column header line: "# Name Address Phone Statement..."
                if in_witness_section and re.match(r'(?i)#\s+Name\s+Address\s+Phone', line):
                    witness_table_mode = True
                    continue

                # Parse numbered table rows: "1 Shirley Murphy 6413 Jefferson Pkwy, TX (545) 736-9977 Statement..."
                if witness_table_mode:
                    row_match = re.match(r'^(\d+)\s+(.+)', line)
                    if row_match:
                        save_witness()
                        rest = row_match.group(2)
                        # Use phone as anchor to split name+address from statement
                        phone_m = re.search(r'(\(\d{3}\)\s*\d{3}[-\s]\d{4})', rest)
                        if phone_m:
                            before_phone = rest[:phone_m.start()].strip()
                            phone = phone_m.group(1)
                            statement = rest[phone_m.end():].strip()
                            # Split name vs address: name ends before first house number (digit)
                            addr_start = re.search(r'\s+\d', before_phone)
                            if addr_start:
                                name = before_phone[:addr_start.start()].strip()
                                address = before_phone[addr_start.start():].strip()
                            else:
                                parts_w = before_phone.split()
                                name = ' '.join(parts_w[:2]) if len(parts_w) >= 2 else before_phone
                                address = ' '.join(parts_w[2:]) if len(parts_w) > 2 else "Unknown"
                            current_entity = {"name": name, "address": address,
                                              "phone": phone, "statement": statement}
                        else:
                            # No phone found — best-effort name extraction
                            parts_w = rest.split()
                            name = ' '.join(parts_w[:2]) if len(parts_w) >= 2 else rest
                            current_entity = {"name": name}
                        continue
                    elif re.match(r'(?i)Investigating\s+Officer|Reviewing\s+Supervisor|Report\s+Status', line):
                        # End of witness table — officer sign-off begins
                        witness_table_mode = False
                        in_witness_section = False
                        save_witness()
                        continue

                # Named witness delimiter formats: "W1:", "Witness 1:"
                w_match = re.match(
                    r'(?i)(?:#\s*:\s*W\d+|Witness\s*[#]?\s*\d+\s*[:\s]?|W\d+\s*[:\s])',
                    line
                )
                if w_match:
                    save_witness()
                    current_entity = {}
                    rest = line[w_match.end():].strip()
                    if rest:
                        parts = re.split(r'\s*[—–]{1,2}\s*|\s+-\s+', rest)
                        if parts[0].strip():
                            current_entity["name"] = parts[0].strip()
                        if len(parts) > 1:
                            p1 = parts[1].strip()
                            if re.search(r'[\d\(\)\-\+]{7,}', p1):
                                current_entity["phone"] = p1
                            else:
                                current_entity["statement"] = p1
                        if len(parts) > 2:
                            current_entity.setdefault("statement", parts[2].strip())
                    continue

                if not (in_witness_section or witness_table_mode or current_entity):
                    continue

                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()

                    if "name" in key:
                        current_entity["name"] = val
                    elif "dob" in key or "date of birth" in key or "birth" in key:
                        current_entity["dob"] = val
                    elif "address" in key or "addr" in key:
                        current_entity["address"] = val
                    elif "phone" in key or "tel" in key or "cell" in key:
                        current_entity["phone"] = val
                    elif "statement" in key:
                        current_entity["statement"] = val

            save_witness()
            result_list = witnesses

        if not result_list:
            return []

        json_val = json.dumps(result_list)
        return [
            Candidate(
                field_id=field_id,
                value=json_val,
                confidence=1.0,
                source_strategy="advanced_table",
                page=1,
                metadata={"reason": f"Extracted {cfg.table_type} via advanced table strategy"}
            )
        ]
