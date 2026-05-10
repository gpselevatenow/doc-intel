# ClaimsIntel VPC: Document Extraction Suite

ClaimsIntel VPC is a deterministic, template-driven Document Intelligence platform. It is designed to securely extract, validate, and visualize structured data from complex documents like Police Reports and Independent Adjuster (IA) Reports. 

Instead of relying on unpredictable LLMs, the system uses an intelligent mix of Machine Learning Layout Analysis, Universal Table Parsing, and Human-in-the-Loop (HITL) continuous learning.

---

## 🛠️ How It Works (Simplified)

1. **Document Upload:** A user uploads a PDF. The frontend visually renders it.
2. **AI Layout Analysis:** A machine learning model "reads" the document like a human, looking for structural elements like paragraphs, bounding boxes, and data tables. It converts the visual document into clean Markdown text.
3. **Universal Table Extraction:** A custom engine scans the Markdown for tables. It dynamically traces headers and maps data (e.g., finding the "VIN" column regardless of where it is) to extract complex nested objects like Vehicles and Parties.
4. **Validation & Review:** The extracted data is compared against a strict JSON rulebook. If required fields are missing, the system flags them so the frontend can display red "Needs Review" badges.
5. **Continuous Learning:** If the user manually corrects a field in the UI, a background script traces the correction back to the original document, learns the new column header alias, and permanently gets smarter for the next run!

---

## 🏗️ Technology Stack & Components

### 1. The Frontend (User Interface)
* **React & Vite:** Drives the fast, interactive user interface.
* **PDF.js (`@react-pdf-viewer`):** Renders the actual PDF document on screen. We use a custom bounding box plugin to draw geometric highlights directly over extracted text.

### 2. The Backend (API Server)
* **FastAPI:** The high-performance Python web framework that orchestrates the extraction pipeline, manages file uploads, and serves the REST API.
* **SQLite (`feedback.db`):** A lightweight local database used entirely for storing Human-in-the-Loop corrections and tracking dynamically learned table headers.

### 3. The ML Engine (OCR & Parsing)
* **Docling & RapidOCR:** The heavy-lifting Machine Learning layer. It uses PyTorch models to perform Document Layout Analysis (DLA). Used strictly to convert PDF pixels into structured Markdown grids and calculate physical `[x,y]` coordinates for the frontend highlights.

### 4. The Extraction Engine (Data Mapping)
* **Python (Regex & 2D Arrays):** Used in `police_extractor.py`. Fast, deterministic logic that parses markdown grids dynamically based on row/column intersections.
* **JSON Template Engine:** JSON files (`police_report.json`) that act as strict Schema Orchestrators. They define exactly what fields are required to pass validation.

---

## ✅ What the Solution CAN Do

* **Universal Table Extraction:** Dynamically reads nested data (Vehicles, Parties, Witnesses) from *any* format, as long as the data is in a grid/table with recognizable column headers. It does not care about column order or span formatting.
* **Automated Continuous Learning (HITL):** If a specific police precinct uses a strange column header (e.g., "Tag No." instead of "License Plate"), the system traces the adjuster's manual UI correction back to the document and permanently learns the new alias!
* **Structured Fallbacks:** If a table is entirely broken, the system safely falls back to Regex scanning to scrape known patterns (like 17-character VINs) from paragraphs.
* **Validation & Highlighting:** Strictly enforces data completeness and calculates physical `[x,y]` coordinates for visual highlighting.

## ❌ What the Solution CANNOT Do

* **Extract Complex Relationships from Pure Paragraphs:** If a report writes out a massive narrative paragraph like *"Driver 1 (John) was driving Vehicle 2 (Ford) and hit Driver 3 (Jane)"*, the system cannot map those relationships. It relies on grid structures for nested arrays. Heavy NLP models would be required for pure narrative logic.
* **Read Heavy Cursive / Bad Scans Reliably:** The underlying AI OCR engine is optimized for printed text. Heavy, messy handwritten officer notes or 3rd-generation faxes will likely yield garbled text, triggering a manual "Needs Review" flag.
* **Auto-Trigger Background Learning Instantly:** The learning script (`train_feedback.py`) does not execute the millisecond a user clicks "save" in the UI (to prevent database locks). It is designed to be run as a background task or CRON job.

---

## 🚀 Getting Started

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
