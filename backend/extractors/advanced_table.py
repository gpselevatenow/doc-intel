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
                "make": ["make", "manufacturer"],
                "year": ["year", "yr"],
                "model": ["model", "mod"],
                "color": ["color", "col"],
                "damages": ["damage", "damages", "severity"],
                "owner_name": ["owner name", "owner"],
                "owner_address": ["owner address", "owner addr", "owner street"],
                "insurance_company": ["insurance", "insurance company", "carrier"],
                "policy_number": ["policy", "policy number", "policy no"],
                "towed": ["towed", "tow"],
                "towing_company": ["towing company", "towed by", "tower"],
                "year_make_model": ["year / make / model", "year/make/model", "make/model/year"]
            }
            vehicles_dict = {}
            lines = text.splitlines()
            current_entity = {}
            current_id = None

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
                if not line:
                    continue

                # Match: V1, V2:, Vehicle 1, Vehicle #1, #: V1, VEHICLE 2, etc.
                v_match = re.search(
                    r'(?i)(?:^|\b)(?:#\s*:\s*V(\d+)|Vehicle\s*[#]?\s*(\d+)\s*[:\s]|V(\d+)\s*[:]\s*)',
                    line
                )
                if v_match:
                    save_vehicle()
                    num = v_match.group(1) or v_match.group(2) or v_match.group(3)
                    current_id = f"V{num}" if num else v_match.group(0).strip()
                    current_entity = {}
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
                            else:
                                current_entity[target_key] = val
                            break

            save_vehicle()
            result_list = list(vehicles_dict.values())

        elif cfg.table_type == "parties":
            parties = []
            current_entity = {}
            lines = text.splitlines()

            def save_party():
                nonlocal current_entity
                if not current_entity:
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
                if not line:
                    continue

                # Match: Party:, Party 1:, PARTY:, Operator:, Driver:, Passenger:, Veh: V1
                party_match = re.match(
                    r'(?i)(Party\s*[#]?\s*\d*\s*:?|Veh\s*:\s*V\d+|Operator\s*[#]?\s*\d*\s*:|Driver\s*[#]?\s*\d*\s*:|Passenger\s*[#]?\s*\d*\s*:)',
                    line
                )
                if party_match:
                    save_party()
                    current_entity = {}
                    delimiter_found = True
                    full_line_lower = line.lower()
                    if "driver" in full_line_lower or "operator" in full_line_lower:
                        current_entity["role"] = "Operator"
                    elif "passenger" in full_line_lower:
                        current_entity["role"] = "Passenger"
                    elif full_line_lower.startswith("veh"):
                        current_entity["role"] = "Passenger"
                    continue

                if not delimiter_found:
                    continue

                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()

                    if key in ("role", "party role", "party type"):
                        current_entity["role"] = val
                    elif "name" in key:
                        current_entity["name"] = val
                    elif "dob" in key or "date of birth" in key or "birth" in key:
                        current_entity["dob"] = val
                    elif "address" in key or "addr" in key:
                        current_entity["address"] = val
                    elif any(k in key for k in ("license", "dl #", "dl#", "driver lic", "driver's lic")):
                        current_entity["license_number"] = val
                    elif "injury" in key or "condition" in key:
                        current_entity["condition"] = val
                    elif any(k in key for k in ("alcohol", "drug", "substance", "dui")):
                        current_entity["condition"] = (current_entity.get("condition", "") + " " + val).strip()
                    elif "transport" in key or "taken to" in key or "hospital" in key:
                        current_entity["transported_to"] = val
                        current_entity["_transported_flag"] = True
                    elif "citation" in key or "charge" in key or "infraction" in key:
                        existing = current_entity.get("citations", "")
                        current_entity["citations"] = (existing + ", " + val).strip(", ") if existing else val
                    elif "passenger" in key:
                        current_entity["role"] = "Passenger"
                    elif "operator" in key or "driver" in key:
                        current_entity["role"] = "Operator"

            save_party()
            result_list = parties

        elif cfg.table_type == "witnesses":
            witnesses = []
            current_entity = {}
            lines = text.splitlines()

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

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Match: W1, W2:, Witness 1, Witness #1, #: W1
                w_match = re.match(
                    r'(?i)(?:#\s*:\s*W\d+|Witness\s*[#]?\s*\d+\s*[:\s]?|W\d+\s*[:\s])',
                    line
                )
                if w_match:
                    save_witness()
                    current_entity = {}
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
