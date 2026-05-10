import re

def clean_text_for_paragraph(text: str) -> str:
    # Remove markdown special characters, keep only alphanumerics, spaces, and basic punctuation
    text = re.sub(r'[^a-zA-Z0-9\s\.,\$\-\(\)]', '', text)
    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_ia_report(text: str) -> dict:
    # Regex fallback strategy for exact matching without LLMs.
    cause_match = re.search(r'(?i)cause of loss(?:[:\s]+)?([A-Za-z ]{2,30})', text)
    cause = cause_match.group(1).strip() if cause_match else "Unknown"
    
    insp_match = re.search(r'(?i)date of inspection(?:[:\s]+)?([\d-]+)', text)
    insp_date = insp_match.group(1) if insp_match else "Unknown Date"
    
    cov_a = re.search(r'(?i)coverage a(?:[:\s]+)?([\$\d,\.]+)', text)
    cov_a_val = cov_a.group(1) if cov_a else "N/A"
    
    cov_b = re.search(r'(?i)coverage b(?:[:\s]+)?([\$\d,\.]+)', text)
    cov_b_val = cov_b.group(1) if cov_b else "N/A"
    
    cov_c = re.search(r'(?i)coverage c(?:[:\s]+)?([\$\d,\.]+)', text)
    cov_c_val = cov_c.group(1) if cov_c else "N/A"
    
    cov_d = re.search(r'(?i)coverage d(?:[:\s]+)?([\$\d,\.]+)', text)
    cov_d_val = cov_d.group(1) if cov_d else "N/A"
    
    subro = re.search(r'(?i)subrogation(?:[:\s]+)?(yes|no|potential)', text)
    subro_val = subro.group(1).title() if subro else "Unknown"
    
    settlement_match = re.search(r'(?i)settlement (?:is|estimated at) ([\$\d,\.]+)', text)
    settlement_val = settlement_match.group(1) if settlement_match else "Not estimated"

    officials = []
    if re.search(r'(?i)fire department', text):
        officials.append("fire department")
    if re.search(r'(?i)police', text):
        officials.append("police")
    officials_str = f" Officials responding included the {' and '.join(officials)}." if officials else " No officials responded."

    policy_form = "Unknown Policy Form"
    pf_match = re.search(r'(?i)policy form(?:[:\s]+)?([A-Za-z0-9]+)', text)
    if pf_match: policy_form = pf_match.group(1)

    raw_summary = (f"The cause of loss is {cause}. "
                   f"Coverage A is {cov_a_val} (Inspection Date: {insp_date}, Firm: Unknown Firm). "
                   f"Coverage B is {cov_b_val}. "
                   f"Coverage C is {cov_c_val}. "
                   f"Coverage D is {cov_d_val}. "
                   f"Coverages include {policy_form}. "
                   f"The settlement is estimated at {settlement_val}. "
                   f"Subrogation status is {subro_val}."
                   f"{officials_str} "
                   f"Summary of payments made to date: Data pending ClaimCenter integration.")
    
    summary = clean_text_for_paragraph(raw_summary)
    
    if "reserve" in text.lower():
        summary = "WARNING: RESERVE INCLUDED " + summary
        
    score = 0
    reasons = []
    
    if cause != "Unknown": 
        score += 1
        reasons.append("Found Cause of Loss")
    else: reasons.append("Missing Cause of Loss")
        
    if insp_date != "Unknown Date": 
        score += 1
        reasons.append("Found Inspection Date")
    else: reasons.append("Missing Inspection Date")
        
    if cov_a_val != "N/A": 
        score += 1
        reasons.append("Found Coverage A")
    else: reasons.append("Missing Coverage A")
        
    if subro_val != "Unknown": 
        score += 1
        reasons.append("Found Subrogation Status")
    else: reasons.append("Missing Subrogation Status")
        
    if settlement_val != "Not estimated": 
        score += 1
        reasons.append("Found Settlement Estimate")
    else: reasons.append("Missing Settlement Estimate")
    
    accuracy_score = (score / 5.0) * 100.0

    return {
        "accuracy_score": round(accuracy_score, 1),
        "accuracy_reasons": reasons,
        "summary": summary,
        "cause_of_loss": cause,
        "coverage_a": cov_a_val,
        "coverage_b": cov_b_val,
        "coverage_c": cov_c_val,
        "coverage_d": cov_d_val,
        "settlement": settlement_val,
        "subrogation": subro_val
    }
