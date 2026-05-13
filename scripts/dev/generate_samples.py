import os
try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf"])
    from fpdf import FPDF

def create_pdf(filename, title, content_lines):
    pdf = FPDF()
    pdf.add_page()
    
    # Draw a white background to prevent black pages in browser dark mode
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    for line in content_lines:
        pdf.multi_cell(0, 10, txt=line)
        
    pdf.output(filename)

def main():
    out_dir = "sample_documents"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # 1. IA Report - Low Complexity
    create_pdf(
        os.path.join(out_dir, "IA_Report_Low_Complexity.pdf"),
        "INDEPENDENT ADJUSTER REPORT",
        [
            "File Number: 12345-LOW",
            "Date of Inspection: 2026-05-10",
            "",
            "Cause of Loss: Hail Damage",
            "The property was inspected on site. The roof sustained significant damage from a recent hailstorm.",
            "",
            "Coverage A: $150,000",
            "Coverage B: $15,000",
            "Coverage C: $75,000",
            "Coverage D: $30,000",
            "",
            "The settlement is estimated at $45,000 to cover the roof replacement and interior water damage.",
            "",
            "Subrogation: No",
            "No third party is responsible for this weather event."
        ]
    )

    # 2. IA Report - High Complexity (Tests missing coverages & reserve trigger)
    create_pdf(
        os.path.join(out_dir, "IA_Report_High_Complexity.pdf"),
        "INDEPENDENT ADJUSTER REPORT - FIELD NOTES",
        [
            "File Number: 99887-HIGH",
            "Date of Inspection: 2026-05-11",
            "",
            "Initial Assessment:",
            "The insured reported a kitchen fire. Cause of loss: Kitchen Fire. The fire department responded quickly, but smoke damage is extensive.",
            "",
            "Policy Details:",
            "Coverage A: $350,000",
            "Coverage C: $120,000",
            "(Note: Detached structures and loss of use are not listed on the primary declaration page.)",
            "",
            "Financials:",
            "Please ensure we set a reserve for the upcoming living expenses.",
            "Based on contractor bids, the settlement is estimated at $85,500.",
            "",
            "Subrogation: Potential",
            "We are investigating the manufacturer of the toaster oven."
        ]
    )

    # 3. Police Report - Low Complexity
    create_pdf(
        os.path.join(out_dir, "Police_Report_Low_Complexity.pdf"),
        "POLICE COLLISION REPORT",
        [
            "Incident Date/Time: 2026-05-01 14:30",
            "Location: Main St and 1st Ave",
            "Weather: Clear",
            "",
            "Accident Type: Rear End",
            "Vehicle 1 failed to stop in time.",
            "",
            "Involved Vehicles:",
            "Vehicle 1 VIN: 1G1RC6E42BU111111",
            "Vehicle 1 Plate: ABC1234",
            "",
            "EMS Involvement: No ambulance was required."
        ]
    )

    # 4. Police Report - Medium Complexity (Tests State Codes)
    create_pdf(
        os.path.join(out_dir, "Police_Report_Medium_Complexity.pdf"),
        "STATE HIGHWAY PATROL REPORT",
        [
            "Incident Date/Time: 2026-05-02 22:15",
            "Location: I-95 Northbound, Mile Marker 42",
            "Weather: Raining",
            "",
            "Accident Type: Sideswipe",
            "",
            "Involved Vehicles:",
            "Vehicle 1 VIN: 2T1BURHE3BC222222 Plate: XYZ9876",
            "Vehicle 2 VIN: 3VWDB7AJ4CM333333 Plate: LMN4567",
            "",
            "Citation Information:",
            "Driver of Vehicle 1 was cited for Code 11 and subsequently for Code 9-2 after failing a field sobriety test.",
            "Vehicle 1 insurance provided: Code 104",
            "",
            "EMS transported Driver 2 to the hospital."
        ]
    )

    # 5. Police Report - High Complexity (Tests noisy data & multiple state codes)
    create_pdf(
        os.path.join(out_dir, "Police_Report_High_Complexity.pdf"),
        "OFFICIAL CRASH REPORT - DETAILED",
        [
            "Incident Date/Time: 2026-05-05 08:00",
            "Location: Downtown Intersection - Broad & High",
            "Weather: Snowing",
            "",
            "Accident Type: Head On",
            "Multiple vehicles involved in a pileup due to slick conditions.",
            "",
            "Vehicle List:",
            "V1: Make Ford | VIN 1FMCU0EG1DU444444 | Plate QWE1111",
            "V2: Make Honda | VIN JHMZC5F57CC555555 | Plate RTY2222",
            "V3: Make Toyota | VIN 4T1B11HK5EU666666 | Plate UIO3333",
            "",
            "Narrative:",
            "V1 lost control. V2 attempted to swerve but collided head on. V3 rear-ended V2.",
            "State Codes noted in ledger: 12 (Reckless behavior), 44 (Failure to yield right of way).",
            "EMS was dispatched. Ambulance transported 3 individuals."
        ]
    )

    print("Successfully generated 5 sample PDF documents in the 'sample_documents' folder.")

if __name__ == "__main__":
    main()
