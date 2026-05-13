from fpdf import FPDF
import os
import random

PAGE_COUNTS = [10, 15, 25, 35, 50]
OUTPUT_DIR = "test_documents"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_pdf(pages, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for i in range(pages):
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Alternating Police and IA report content randomly to simulate complex data
        report_type = random.choice(["Police Report", "IA Report"])

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"{report_type} - PAGE {i + 1}", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        if report_type == "Police Report":
            pdf.cell(200, 10, txt=f"Accident Type: {random.choice(['Rear-end Collision', 'Head-on Collision', 'Sideswipe', 'Unknown'])}", ln=True)
            pdf.cell(200, 10, txt=f"Date/Time: 2023-10-{random.randint(10,31)} 14:30", ln=True)
            pdf.cell(200, 10, txt=f"Location: {random.randint(100,999)} Main St, Cityville", ln=True)
            pdf.cell(200, 10, txt=f"Weather: {random.choice(['Clear', 'Rain', 'Snow', 'Fog'])}", ln=True)
            pdf.cell(200, 10, txt="EMS Agency: City Rescue Squad (Transported: Yes)", ln=True)
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Vehicle 1 Information", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"VIN: 1G1RC6E42BU{random.randint(100000,999999)}", ln=True)
            pdf.cell(200, 10, txt="Make/Model: Toyota Camry", ln=True)
            pdf.cell(200, 10, txt="Damages: Front Bumper Crushed, Airbag Deployed", ln=True)
            
            # Simulated Data Grid / Noise
            for _ in range(20):
                pdf.cell(200, 10, txt="Additional investigative notes indicating severity of impact and witness statements.", ln=True)

        else:
            pdf.cell(200, 10, txt=f"Cause of Loss: {random.choice(['Fire', 'Water Damage', 'Wind/Hail', 'Vandalism'])}", ln=True)
            pdf.cell(200, 10, txt="Inspection Date: 2023-11-05", ln=True)
            pdf.cell(200, 10, txt="Firm: Independent Adjusting Group LLC", ln=True)
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Coverage Breakdown", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Coverage A (Dwelling): ${random.randint(50,500)},000", ln=True)
            pdf.cell(200, 10, txt="Coverage B (Other Structures): N/A", ln=True)
            pdf.cell(200, 10, txt="Subrogation: Under Investigation", ln=True)
            pdf.cell(200, 10, txt="Settlement: Recommended at $45,000", ln=True)
            
            if random.random() > 0.8:
                pdf.set_text_color(255, 0, 0)
                pdf.cell(200, 10, txt="WARNING: RESERVE INCLUDED in this documentation.", ln=True)
                pdf.set_text_color(0, 0, 0)

            # Simulated filler text to add page length
            for _ in range(25):
                pdf.cell(200, 10, txt="Detailed structural analysis. Water lines ruptured behind the drywall.", ln=True)

    pdf.output(os.path.join(OUTPUT_DIR, filename))
    print(f"Generated: {filename} ({pages} pages)")

if __name__ == "__main__":
    print("Generating bulk PDF test suite...")
    for count in PAGE_COUNTS:
        filename = f"StressTest_Document_{count}_Pages.pdf"
        generate_pdf(count, filename)
    print("Done! PDFs saved to the test_documents directory.")
