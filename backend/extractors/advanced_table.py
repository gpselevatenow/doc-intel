import json
import re
from typing import Any
from pydantic import BaseModel

from core.candidate import Candidate
from core.document_model import Document
from extractors.base import Strategy, register

class AdvancedTableConfig(BaseModel):
    table_type: str # "vehicles", "parties", "witnesses"

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
        
        # We port the robust logic to extract vehicles, parties, and witnesses natively
        def has_word(s: str, w: str) -> bool:
            return re.search(rf'\b{w}\b', s.lower()) is not None
            
        if cfg.table_type == "vehicles":
            aliases = {
                "vin": ["vin", "vehicle identification", "identification number"],
                "plate": ["plate", "license plate", "tag"],
                "make": ["make", "manufacturer"],
                "year": ["year", "yr"],
                "model": ["model", "mod"],
                "color": ["color", "col"],
                "damages": ["damage", "damages", "severity"],
                "owner_name": ["owner", "owner name"],
                "insurance_company": ["insurance", "insurance company", "carrier"],
                "policy_number": ["policy", "policy number"],
                "towed": ["towed", "towed by"],
                "towing_company": ["towing company", "tower"]
            }
            vehicles_dict = {}
            lines = text.splitlines()
            current_entity = {}
            current_id = None
            
            def save():
                nonlocal current_entity, current_id
                if current_id and current_entity:
                    if current_id not in vehicles_dict:
                        vehicles_dict[current_id] = {
                            "vin": "Unknown", "plate": "Unknown", "make": "Unknown",
                            "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
                            "owner_name": "Unknown", "insurance_company": "Unknown",
                            "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
                        }
                    for k, v in current_entity.items():
                        if k != "_id": vehicles_dict[current_id][k] = v
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Match V1, V2, etc.
                v_match = re.search(r'(?i)(?:#:\s*V\d+|Vehicle V\d+)', line)
                if v_match:
                    save()
                    current_id = v_match.group(0)
                    current_entity = {}
                    continue
                    
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()
                    
                    for target_key, alias_list in aliases.items():
                        if any(has_word(key, a) for a in alias_list):
                            current_entity[target_key] = val
                            break
                            
            save()
            result_list = list(vehicles_dict.values())
            
        elif cfg.table_type == "parties":
            parties = []
            current_entity = {}
            lines = text.splitlines()
            
            def save():
                nonlocal current_entity
                if current_entity:
                    parties.append({
                        "name": current_entity.get("name", "Unknown"),
                        "dob": current_entity.get("dob", "Unknown"),
                        "address": current_entity.get("address", "Unknown"),
                        "license_number": current_entity.get("license_number", "Unknown"),
                        "condition": current_entity.get("condition", "Unknown"),
                        "transported_to": current_entity.get("transported_to", "Unknown"),
                        "citations": current_entity.get("citations", "None")
                    })
                    
            for line in lines:
                line = line.strip()
                if not line: continue
                
                if re.match(r'(?i)Party:\s*(.+)', line) or re.match(r'(?i)Veh:\s*V\d+', line):
                    save()
                    current_entity = {}
                    continue
                    
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()
                    
                    if "name" in key: current_entity["name"] = val
                    elif "dob" in key: current_entity["dob"] = val
                    elif "license" in key: current_entity["license_number"] = val
                    elif "injury" in key or "condition" in key: current_entity["condition"] = val
                    elif "transport" in key: current_entity["transported_to"] = val
                    elif "citation" in key: current_entity["citations"] = val
                    elif "address" in key: current_entity["address"] = val
            save()
            result_list = parties
            
        elif cfg.table_type == "witnesses":
            witnesses = []
            current_entity = {}
            lines = text.splitlines()
            
            def save():
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
                if not line: continue
                
                if re.match(r'(?i)#:\s*W\d+', line) or re.match(r'(?i)Witness\s*\d+', line):
                    save()
                    current_entity = {}
                    continue
                    
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()
                    
                    if "name" in key: current_entity["name"] = val
                    elif "dob" in key: current_entity["dob"] = val
                    elif "address" in key: current_entity["address"] = val
                    elif "phone" in key: current_entity["phone"] = val
                    elif "statement" in key: current_entity["statement"] = val
            save()
            result_list = witnesses

        if not result_list:
            return []
            
        # Return as JSON serialized string
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
