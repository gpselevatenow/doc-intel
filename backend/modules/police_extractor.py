import re

def clean_text_for_paragraph(text: str) -> str:
    # Remove markdown special characters, keep only alphanumerics, spaces, and basic punctuation
    text = re.sub(r'[^a-zA-Z0-9\s\.,\$\-\(\)]', '', text)
    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

STATE_CODES = {
    "9-2": "DUI / Operating Under Influence",
    "104": "GEICO",
    "44": "Failure to Yield",
    "11": "Speeding",
    "12": "Reckless Driving"
}

def parse_markdown_tables(text: str):
    tables = []
    lines = text.splitlines()
    in_table = False
    current_table = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if set(cells) == {'-'} or all(c.replace('-', '').strip() == '' for c in cells):
                continue
            if not in_table:
                in_table = True
            current_table.append(cells)
        else:
            if in_table:
                tables.append(current_table)
                in_table = False
                current_table = []
    if in_table:
        tables.append(current_table)
    return tables

def extract_police_report(text: str) -> dict:
    vehicles_dict = {}
    parties = []
    witnesses = []
    
    # --- 1. Universal Markdown Table Extraction ---
    tables = parse_markdown_tables(text)
    for table in tables:
        if not table: continue
        
        header_row_idx = -1
        is_vehicle, is_party, is_witness = False, False, False
        
        for idx, row in enumerate(table):
            row_str = " ".join(row).lower()
            if "vin" in row_str or "plate" in row_str or ("year" in row_str and "make" in row_str):
                header_row_idx = idx
                is_vehicle = True
                break
            elif "license" in row_str or "citation" in row_str or ("party" in row_str and "name" in row_str):
                header_row_idx = idx
                is_party = True
                break
            elif "statement" in row_str or "witness" in row_str or ("name" in row_str and "phone" in row_str):
                # Avoid confusing witness tables with party tables
                if not is_party:
                    header_row_idx = idx
                    is_witness = True
                    break
                    
        if header_row_idx != -1:
            headers = [h.lower() for h in table[header_row_idx]]
            data_rows = table[header_row_idx+1:]
            
            if is_vehicle:
                for row in data_rows:
                    row_data = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                    
                    vin = "Unknown"
                    for h in headers:
                        if "vin" in h: vin = row_data[h]
                    if vin == "Unknown" or vin == "": continue
                    
                    v = {
                        "vin": vin, "plate": "Unknown", "make": "Unknown",
                        "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
                        "owner_name": "Unknown", "owner_address": "Unknown", "insurance_company": "Unknown",
                        "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
                    }
                    for k, val in row_data.items():
                        if "plate" in k: v["plate"] = val
                        elif "damage" in k: v["damages"] = val
                        elif "make" in k or "year" in k: v["make"] = val
                    vehicles_dict[vin] = v
                    
            elif is_party:
                for row in data_rows:
                    row_data = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                    name = "Unknown"
                    for h in headers:
                        if "name" in h: name = row_data[h]
                    if name == "Unknown" or name == "": continue
                    
                    p = {
                        "name": name, "dob": "Unknown", "address": "Unknown",
                        "license_number": "Unknown", "condition": "Unknown", 
                        "transported_to": "Unknown", "citations": "None"
                    }
                    for k, val in row_data.items():
                        if "dob" in k: p["dob"] = val
                        elif "license" in k: p["license_number"] = val
                        elif "citation" in k: p["citations"] = val
                        elif "injury" in k or "condition" in k: p["condition"] = val
                        elif "transport" in k: p["transported_to"] = val
                        elif "address" in k: p["address"] = val
                    parties.append(p)
                    
            elif is_witness:
                for row in data_rows:
                    row_data = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                    name = "Unknown"
                    for h in headers:
                        if "name" in h: name = row_data[h]
                    if name == "Unknown" or name == "": continue
                    
                    w = {
                        "name": name, "dob": "Unknown", "address": "Unknown",
                        "phone": "Unknown", "statement": "Unknown"
                    }
                    for k, val in row_data.items():
                        if "dob" in k: w["dob"] = val
                        elif "address" in k: w["address"] = val
                        elif "phone" in k: w["phone"] = val
                        elif "statement" in k: w["statement"] = val
                    witnesses.append(w)

    # --- 2. Fallback: Block Parser (For Flattened Tables) ---
    current_block_type = None
    current_entity = {}

    def save_entity():
        if current_block_type == "vehicle" and current_entity:
            vin = current_entity.get("vin", "Unknown")
            vid = current_entity.get("_id", "Unknown")
            if vin == "Unknown" and vid != "Unknown": vin = f"Unknown_{vid}"
            
            if vin not in vehicles_dict:
                vehicles_dict[vin] = {
                    "vin": vin, "plate": "Unknown", "make": "Unknown",
                    "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
                    "owner_name": "Unknown", "owner_address": "Unknown", "insurance_company": "Unknown",
                    "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
                }
            for k, v in current_entity.items():
                if k != "_id": vehicles_dict[vin][k] = v
        elif current_block_type == "party" and current_entity:
            parties.append({
                "name": current_entity.get("name", "Unknown"),
                "dob": current_entity.get("dob", "Unknown"),
                "address": current_entity.get("address", "Unknown"),
                "license_number": current_entity.get("license", "Unknown"),
                "condition": current_entity.get("injury", "Unknown"),
                "transported_to": current_entity.get("transported", "Unknown"),
                "citations": current_entity.get("citation", "None")
            })
        elif current_block_type == "witness" and current_entity:
            witnesses.append({
                "name": current_entity.get("name", "Unknown"),
                "dob": current_entity.get("dob", "Unknown"),
                "address": current_entity.get("address", "Unknown"),
                "phone": current_entity.get("phone", "Unknown"),
                "statement": current_entity.get("statement", "Unknown")
            })

    # Only run block parser if markdown tables didn't catch anything
    if not vehicles_dict and not parties and not witnesses:
        for line in text.splitlines():
            line = line.strip()
            if not line: continue
            
            if re.match(r'(?i)#:\s*V\d+', line):
                save_entity()
                current_block_type = "vehicle"
                current_entity = {"_id": line.split(":")[-1].strip()}
                continue
            elif re.match(r'(?i)Party:\s*(.+)', line):
                save_entity()
                current_block_type = "party"
                current_entity = {}
                continue
            elif re.match(r'(?i)Veh:\s*V\d+', line):
                save_entity()
                current_block_type = "party"
                current_entity = {}
                continue
            elif re.match(r'(?i)#:\s*W\d+', line):
                save_entity()
                current_block_type = "witness"
                current_entity = {}
                continue
                
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip().lower()
                val = parts[1].strip()
                
                if current_block_type == "vehicle":
                    if "vin" in key: current_entity["vin"] = val
                    elif "plate" in key: current_entity["plate"] = val
                    elif "damage" in key: current_entity["damages"] = val
                    elif "year / make / model" in key or "make" in key: current_entity["make"] = val
                elif current_block_type in ["party", "witness"]:
                    if key == "name": current_entity["name"] = val
                    elif key == "dob": current_entity["dob"] = val
                    elif "license" in key: current_entity["license"] = val
                    elif "citation" in key: current_entity["citation"] = val
                    elif "injury" in key: current_entity["injury"] = val
                    elif "transport" in key: current_entity["transported"] = val
                    elif key == "address": current_entity["address"] = val
                    elif key == "phone": current_entity["phone"] = val
                    elif key == "statement": current_entity["statement"] = val
        save_entity()

    vehicles = list(vehicles_dict.values())
    
    if not vehicles:
        vin_matches = list(set(re.findall(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)))
        for idx, vin in enumerate(vin_matches):
            vehicles.append({
                "vin": vin, "plate": "Unknown", "make": "Unknown",
                "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
                "owner_name": "Unknown", "owner_address": "Unknown", "insurance_company": "Unknown",
                "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
            })
    
    # 3. Flat Field Lookups
    found_codes = []
    for code, desc in STATE_CODES.items():
        if re.search(rf'\b{code}\b', text):
            found_codes.append({"code": code, "description": desc})
            
    weather = "Unknown"
    w_match = re.search(r'(?i)Weather[ \t:]*([A-Za-z \t\(\)]+)', text)
    if w_match: weather = w_match.group(1).strip()
    elif re.search(r'(?i)(clear|sunny|raining|snowing|cloudy|rain)', text):
        weather = re.search(r'(?i)(clear|sunny|raining|snowing|cloudy|rain)', text).group(1).capitalize()
        
    ems_agency = "Unknown EMS Agency"
    ems_match = re.search(r'(?i)(?:EMS Agency|Transported)[ \t:]*([A-Za-z0-9 \t,\-]+)', text)
    if ems_match and "No" not in ems_match.group(1): ems_agency = ems_match.group(1).strip()
    elif re.search(r'(?i)(EMS|Ambulance|Hospital|Transported)', text):
        ems_agency = "Dispatched - Unknown Agency"
        
    accident_type = "Unknown"
    a_match = re.search(r'(?i)(?:Accident Type|TYPE OF COLLISION[^\:]*)[ \t:]*([A-Za-z \t\-\(\)\/0-9]+)', text)
    if a_match: accident_type = a_match.group(1).strip()
        
    date_time = "Unknown"
    d_match = re.search(r'(?i)(?:Date/Time|DATE OF INCIDENT)[ \t:]*([A-Za-z0-9 \t,\-]+)', text)
    t_match = re.search(r'(?i)TIME OF INCIDENT[ \t:]*([A-Za-z0-9 \t:]+)', text)
    if d_match:
        date_time = d_match.group(1).strip()
        if t_match: date_time += f" {t_match.group(1).strip()}"
        
    location = "Unknown"
    l_match = re.search(r'(?i)Location[ \t:]*(.*?)(?:\n|$)', text)
    if l_match: location = l_match.group(1).strip()
        
    report_number = "Unknown"
    r_match = re.search(r'(?i)CASE NUMBER[ \t:]*([A-Za-z0-9\-]+)', text)
    if r_match: report_number = r_match.group(1).strip()

    agency = "Unknown Agency"
    officer = "Unknown Officer"

    score = 0
    reasons = []
    if date_time != "Unknown": 
        score += 1
        reasons.append("Found Date/Time")
    else: reasons.append("Missing Date/Time")
        
    if location != "Unknown": 
        score += 1
        reasons.append("Found Location")
    else: reasons.append("Missing Location")
        
    if weather != "Unknown": 
        score += 1
        reasons.append("Found Weather")
    else: reasons.append("Missing Weather")
        
    if accident_type != "Unknown": 
        score += 1
        reasons.append("Found Accident Type")
    else: reasons.append("Missing Accident Type")
        
    if ems_agency != "Unknown EMS Agency": 
        score += 1
        reasons.append("Found EMS Agency")
    else: reasons.append("Missing EMS Agency")
        
    if vehicles and vehicles[0].get("vin", "Unknown") != "Unknown": 
        score += 1
        reasons.append("Found Vehicle details")
    else: reasons.append("Missing Vehicle details")
    
    if agency != "Unknown Agency":
        score += 1
        reasons.append("Found Agency details")
    else: reasons.append("Missing Agency Details")
    
    accuracy_score = (score / 7.0) * 100.0

    raw_summary = (f"A {accident_type} occurred on {date_time} at {location}. "
                   f"The weather was {weather}. "
                   f"The responding agency was {agency} and the investigating officer was {officer} (Report {report_number}). "
                   f"{ems_agency} was dispatched to the scene. "
                   f"There were {len(vehicles)} vehicles involved. "
                   f"Witnesses included {len(witnesses)} individuals. "
                   f"Data processed for ClaimCenter integration.")
                   
    summary = clean_text_for_paragraph(raw_summary)

    return {
        "summary": summary,
        "accuracy_score": round(accuracy_score, 1),
        "accuracy_reasons": reasons,
        "date_time": date_time,
        "location": location,
        "weather": weather,
        "accident_type": accident_type,
        "ems_agency": ems_agency,
        "agency": agency,
        "officer": officer,
        "report_number": report_number,
        "vehicles": vehicles,
        "parties": parties,
        "witnesses": witnesses,
        "state_codes": found_codes
    }
