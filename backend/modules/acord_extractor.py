import re

def clean_text_for_paragraph(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9\s\.,\$\-\(\)]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_acord_report(text: str) -> dict:
    # Deterministic RegEx fallback for structured forms
    agency_match = re.search(r'(?i)(?:agency|producer)(?:[:\s]+)?([A-Za-z\s,]+(?:Inc\.|LLC)?)(?=\n|policy|insured)', text)
    agency = agency_match.group(1).strip() if agency_match else "Unknown Agency"
    
    carrier_match = re.search(r'(?i)company(?:[:\s]+)?([A-Za-z\s,]+(?:Insurance|Mutual|Group)?)(?=\n|policy|insured)', text)
    carrier = carrier_match.group(1).strip() if carrier_match else "Unknown Carrier"
    
    policy_match = re.search(r'(?i)policy number(?:[:\s]+)?([A-Z0-9-]+)', text)
    policy = policy_match.group(1).strip() if policy_match else "Unknown Policy"
    
    insured_match = re.search(r'(?i)named insured(?:[:\s]+)?([A-Za-z\s,]+)(?=\n|date|location)', text)
    insured = insured_match.group(1).strip() if insured_match else "Unknown Insured"
    
    date_match = re.search(r'(?i)date of loss(?:[:\s]+)?([\d\/\-]+)', text)
    date_of_loss = date_match.group(1).strip() if date_match else "Unknown Date"
    
    desc_match = re.search(r'(?i)description of loss(?:[:\s]+)?(.*?)(?=\n[A-Z\s]+:|signature|$)', text, re.DOTALL)
    desc_of_loss = desc_match.group(1).strip() if desc_match else "No description provided"
    
    # Generate Natural Language File Note for Guidewire
    raw_summary = (f"ACORD Property Loss Notice received from {agency}. "
                   f"The carrier is {carrier} under Policy #{policy} for Named Insured {insured}. "
                   f"The Date of Loss is reported as {date_of_loss}. "
                   f"Reported Description: {desc_of_loss}")
                   
    summary = clean_text_for_paragraph(raw_summary)
    
    # Calculate extraction accuracy score
    score = 0
    reasons = []
    
    if agency != "Unknown Agency":
        score += 1
        reasons.append("Found Agency Name")
    else: reasons.append("Missing Agency Name")
        
    if policy != "Unknown Policy":
        score += 1
        reasons.append("Found Policy Number")
    else: reasons.append("Missing Policy Number")
        
    if insured != "Unknown Insured":
        score += 1
        reasons.append("Found Named Insured")
    else: reasons.append("Missing Named Insured")
        
    if date_of_loss != "Unknown Date":
        score += 1
        reasons.append("Found Date of Loss")
    else: reasons.append("Missing Date of Loss")
        
    if desc_of_loss != "No description provided":
        score += 1
        reasons.append("Found Description of Loss")
    else: reasons.append("Missing Description of Loss")
        
    accuracy_score = (score / 5.0) * 100.0

    return {
        "accuracy_score": round(accuracy_score, 1),
        "accuracy_reasons": reasons,
        "summary": summary,
        "agency": agency,
        "carrier": carrier,
        "policy_number": policy,
        "named_insured": insured,
        "date_of_loss": date_of_loss,
        "description_of_loss": desc_of_loss
    }
