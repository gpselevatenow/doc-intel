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

def extract_police_report(text: str) -> dict:
    # 1. Vehicles Parsing
    vehicles = []
    # Horizontal Format: "Make Ford | VIN 1FMCU0EG1DU444444 | Plate QWE1111"
    v_lines = re.findall(r'(?i)Make\s+([A-Za-z]+)\s*\|\s*VIN\s+([A-HJ-NPR-Z0-9]{17})\s*\|\s*Plate\s+([A-Z0-9]+)', text)
    for make, vin, plate in v_lines:
        vehicles.append({
            "vin": vin, 
            "plate": plate, 
            "make": make.title(),
            "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
            "owner_name": "Unknown", "owner_address": "Unknown", "insurance_company": "Unknown",
            "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
        })

    # Vertical Format (from flattened tables):
    # #: V1
    # Year / Make / Model: 2018 Subaru Outback
    # VIN: 4S4BSANC9J3245677
    if not vehicles:
        v_blocks = re.split(r'(?i)#:\s*V\d+', text)
        if len(v_blocks) > 1:
            for block in v_blocks[1:]:
                vin_match = re.search(r'(?i)VIN[\s:]*([A-HJ-NPR-Z0-9]{17})', block)
                if vin_match:
                    make_match = re.search(r'(?i)(?:Make|Model)[\s:]*([A-Za-z0-9\s]+)', block)
                    plate_match = re.search(r'(?i)Plate[\s:]*([A-Z0-9\-]+)', block)
                    vehicles.append({
                        "vin": vin_match.group(1),
                        "plate": plate_match.group(1).strip() if plate_match else "Unknown",
                        "make": make_match.group(1).strip() if make_match else "Unknown",
                        "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
                        "owner_name": "Unknown", "owner_address": "Unknown", "insurance_company": "Unknown",
                        "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
                    })

    if not vehicles:
        # Fallback if specific format isn't found
        vin_matches = list(set(re.findall(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)))
        for vin in vin_matches:
            vehicles.append({
                "vin": vin, 
                "plate": "Unknown", 
                "make": "Unknown",
                "year": "Unknown", "model": "Unknown", "color": "Unknown", "damages": "Unknown",
                "owner_name": "Unknown", "owner_address": "Unknown", "insurance_company": "Unknown",
                "policy_number": "Unknown", "towed": "Unknown", "towing_company": "Unknown"
            })
    
    # 2. State Code Lookup
    found_codes = []
    for code, desc in STATE_CODES.items():
        if re.search(rf'\b{code}\b', text):
            found_codes.append({"code": code, "description": desc})
            
    # 3. Weather
    weather = "Unknown"
    w_match = re.search(r'(?i)Weather[ \t:]*([A-Za-z \t\(\)]+)', text)
    if w_match:
        weather = w_match.group(1).strip()
    elif re.search(r'(?i)(clear|sunny|raining|snowing|cloudy|rain)', text):
        weather = re.search(r'(?i)(clear|sunny|raining|snowing|cloudy|rain)', text).group(1).capitalize()
        
    # 4. EMS Agency
    ems_agency = "Unknown EMS Agency"
    ems_match = re.search(r'(?i)(?:EMS Agency|Transported)[ \t:]*([A-Za-z0-9 \t,\-]+)', text)
    if ems_match and "No" not in ems_match.group(1):
        ems_agency = ems_match.group(1).strip()
    elif re.search(r'(?i)(EMS|Ambulance|Hospital|Transported)', text):
        ems_agency = "Dispatched - Unknown Agency"
        
    # 5. Accident Type
    accident_type = "Unknown"
    a_match = re.search(r'(?i)(?:Accident Type|TYPE OF COLLISION[^\:]*)[ \t:]*([A-Za-z \t\-\(\)\/0-9]+)', text)
    if a_match:
        accident_type = a_match.group(1).strip()
        
    # 6. Date/Time
    date_time = "Unknown"
    d_match = re.search(r'(?i)(?:Date/Time|DATE OF INCIDENT)[ \t:]*([A-Za-z0-9 \t,\-]+)', text)
    t_match = re.search(r'(?i)TIME OF INCIDENT[ \t:]*([A-Za-z0-9 \t:]+)', text)
    if d_match:
        date_time = d_match.group(1).strip()
        if t_match:
            date_time += f" {t_match.group(1).strip()}"
        
    # 7. Location
    location = "Unknown"
    l_match = re.search(r'(?i)Location[ \t:]*(.*?)(?:\n|$)', text)
    if l_match:
        location = l_match.group(1).strip()
        
    # 8. Report Number
    report_number = "Unknown"
    r_match = re.search(r'(?i)CASE NUMBER[ \t:]*([A-Za-z0-9\-]+)', text)
    if r_match:
        report_number = r_match.group(1).strip()

    # --- NEW FIELDS FOR USE CASE ---
    agency = "Unknown Agency"
    officer = "Unknown Officer"
    
    parties = [] # Evaluated by Spacy/NLP in full version
    witnesses = []

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
        
    if vehicles and vehicles[0]["vin"] != "Unknown": 
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
