# ClaimsIntel VPC

ClaimsIntel VPC is a deterministic, template-driven Document Intelligence platform. It is designed to securely extract, validate, and visualize structured data from Independent Adjuster (IA) Reports, ACORD forms, and Police Reports within a self-contained local environment—without relying on unpredictable or external LLMs.

## Core Features

- **Geometric BBox Highlighting:** Instead of fuzzy text searches, ClaimsIntel uses exact `[x, y]` coordinate mapping from the PDF canvas to render absolute, pixel-perfect highlight overlays in the React frontend.
- **Declarative Template Engine:** System administrators can define extraction logic using simple JSON files (`templates/police_report.json`), avoiding hardcoded Python logic.
- **Advanced Spatial Strategies:** Employs geometric algorithms (e.g., `spatial_label`) to locate labels like "CASE NUMBER" and dynamically extract values physically located to their right or below, heavily mitigating OCR format variance.
- **Human-in-the-Loop Validation:** An Orchestrator pipeline validates extracted candidates against explicit regex rules. If a field drops below an `auto_accept_threshold` (e.g., a 6-digit report number when 10 are expected), the system flags it in the UI with a warning icon, requiring human review.
- **Dynamic Feature Injection:** Adjusters can add custom fields directly from the UI. The backend automatically injects a `global_regex` rule into the extraction pipeline to extract that exact field in the future.

## Tech Stack

- **Frontend:** React 18, Vite, `@react-pdf-viewer/core`, Vanilla CSS (Glassmorphism)
- **Backend:** FastAPI (Python 3.12), `docling` (document parser)
- **Database:** Local SQLite (`feedback.db`)

## Getting Started

1. Set up the backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

2. Set up the frontend:
```bash
cd frontend
npm install
npm run dev
```

For more detailed technical architecture, refer to `TECHNICAL_SPECIFICATION.md` or `TECHNICAL_SPECIFICATION.pdf`.
