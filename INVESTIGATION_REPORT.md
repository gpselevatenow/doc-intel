# Doc-Intel Investigation Report
**Date:** 2026-05-13 | **Scope:** Read-only discovery | **Investigator:** Claude Sonnet 4.6

---

## Section A: Current OCR Configuration

### A1. EasyOCR Initialization Location
**EasyOCR is not initialized anywhere in the codebase.** No `easyocr.Reader()` or `import easyocr` call exists in any file (backend, frontend, or root). The only document parsing entry point is:

`backend/core/parser.py:29` — `converter = DocumentConverter()` (bare Docling, no OCR config)

### A2. EasyOCR Init Code
Not applicable. EasyOCR is not present in the codebase.

### A3. OCR-Related Packages in Dependency Files
`backend/requirements.txt` contains **no OCR packages**. Full list:

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-multipart==0.0.12
pydantic==2.10.3
docling==2.15.0          ← ML layout analysis; internally pulls EasyOCR as a sub-dep
pdfplumber==0.11.9       ← primary text extraction for police reports (not OCR)
spacy==3.8.14
en-core-web-lg @ ...
```

`easyocr`, `rapidocr`, `rapidocr-onnxruntime`, `paddleocr`, `tesseract`, and `pytesseract` are **all absent** from requirements.txt. EasyOCR arrives only as a transitive dependency pulled in by `docling`.

### A4. Docling Pipeline Configuration
Docling is invoked at `backend/core/parser.py:23–36` with zero configuration:

```python
def parse_document(file_path: str):
    converter = DocumentConverter()          # bare default — no pipeline config
    result = converter.convert(file_path)
    markdown_text = result.document.export_to_markdown()
    raw_dict = result.document.export_to_dict()
    canonical_doc = load_canonical_document(raw_dict)
    canonical_doc.markdown = markdown_text
    return markdown_text, canonical_doc
```

Docling's default pipeline uses EasyOCR internally for scanned/image PDFs. No explicit OCR engine, language list, or resolution settings are configured.

**Important:** For police reports (`/api/extract/police-report`), Docling's output is **discarded** and replaced with a second `pdfplumber` pass (`main.py:337–342`). The actual extraction engine never sees Docling's markdown for police reports — it sees pdfplumber's raw text. Docling output is only used for bbox coordinate tracking.

### A5. Text Layer Quality of Sample Documents
All three tested sample PDFs are **clean digital PDFs** — OCR does not fire on any of them.

| Document | Pages | Text Chars | CID Artifacts | Text Lines | Layer |
|---|---|---|---|---|---|
| `sample_full_report.pdf` | 9 | 20,988 | 0 | 309 | Digital — full text layer |
| `sample_21_fog_5veh_houston.pdf` | 5 | 10,560 | 0 | 149 | Digital — full text layer |
| `Police_Report_High_Complexity.pdf` | 1 | 636 | 0 | 14 | Digital — minimal synthetic |

pdfplumber extracts clean, structured text from all three. EasyOCR (via Docling) does not engage on digital PDFs — it would only engage on image-only/scanned PDFs, none of which are in the sample set.

---

## Section B: Documentation Drift

### B1. "RapidOCR" Occurrences

Found in **README.md only**. Zero occurrences in TECHNICAL_SPECIFICATION.md or any code file.

| File | Line | Context |
|---|---|---|
| `README.md` | 23 | `* **Docling & RapidOCR (PyTorch)**: The Machine Learning layer...` |
| `README.md` | 34 | `B --> C[Docling & RapidOCR Engine]` (Mermaid diagram node) |

RapidOCR is not installed, not imported, and not referenced anywhere in the Python codebase. The README is describing a dependency that does not exist.

### B2. Absolute-Accuracy Claims

| File | Line | Text |
|---|---|---|
| `README.md` | 5 | `"this solution guarantees 100% extraction for recognized fields without relying on unpredictable LLMs"` |
| `README.md` | 56 | `"guaranteeing perfectly normalized output formatting for arrays like vehicles, parties, and witnesses"` |
| `README.md` | 121 | `"100% Extraction Hit Rate for Known Layouts: Due to multi-line fallback patterns..."` |

The pipeline run in Section F shows that even on the three included sample documents (which the README says "simply upload any of these files to see the template extraction engine in action"), 5–9 out of 15 template fields return `None`. The "100% extraction" claim is not supportable.

### B3. Other README/Code Inconsistencies

| Claim | Reality |
|---|---|
| README/TECH SPEC: "Docling & RapidOCR" | RapidOCR not installed; Docling alone is used |
| TECH SPEC line 12: "React 18" | `frontend/package.json`: `"react": "^19.2.5"` — actually React 19 |
| TECH SPEC line 56: `spatial_label` strategy is "supported" | `spatial_label.py` exists but `police_report.json` and `ia_report.json` both use only `global_regex` and `advanced_table` — `spatial_label` is not in any deployed template |
| README: BBox highlighting proves "exactly where data came from" | For police reports, the orchestrator extracts from pdfplumber text (`main.py:337–342`), not Docling output. Docling bboxes track Docling's parse, not the regex match location. Bbox mapping is unreliable for police report fields. |
| README: "over 40 diverse PDF reports" in `/sample documents/` | Not verified, but the README implies these all work — the pipeline run shows date_time and location return `None` on two of three tested samples |
| `acord_report.json` template | Empty `"fields": []` — the ACORD extraction path (`/api/extract/acord-report`) does NOT use the template engine; it calls the hardcoded `modules/acord_extractor.py` module and only uses the orchestrator for dynamic custom fields |

---

## Section C: Repo Hygiene

### C1. `feedback.db` Git Tracking

`feedback.db` **IS tracked in git** at the repo root. `git ls-files` output:

```
feedback.db          ← root-level, TRACKED (should not be)
backend/train_feedback.py
```

The `.gitignore` ignores `backend/feedback.db` but **not** the root-level `feedback.db`. The code (`backend/database.py:5`) resolves the DB path as `os.path.join(os.path.dirname(os.path.abspath(__file__)), "feedback.db")`, which resolves to `backend/feedback.db` — the one that is gitignored. The tracked root `feedback.db` is a stale orphan from before the `backend/` refactor.

### C2. `feedback.db` Schema and Row Counts

There are **two** feedback.db files. The operational one is `backend/feedback.db`.

**Root `feedback.db`** (tracked by git, stale):
| Table | Rows |
|---|---|
| `corrections` | 0 |
| `custom_fields` | 0 |

**`backend/feedback.db`** (active, gitignored):
| Table | Rows | Notes |
|---|---|---|
| `corrections` | 0 | No user corrections logged yet |
| `custom_fields` | 0 | No custom fields added yet |
| `raw_documents` | 47 | 47 documents processed and stored |
| `table_aliases` | 0 | Alias learning has not fired |
| `user_feedback` | 8 | 8 thumbs-up/down ratings |
| `learned_patterns` | 1 | 1 pattern learned from feedback |

### C3. `.gitignore` Contents (full)

```gitignore
# Python
backend/venv/
**/__pycache__/
**/*.pyc
backend/feedback.db

# Node / React
frontend/node_modules/
frontend/dist/
frontend/.env.local
frontend/.env.development.local
frontend/.env.test.local
frontend/.env.production.local

# Documents / Sensitive Info
*.pdf
!sample documents/*.pdf
!sample_documents/*.pdf
*.docx
*.txt
scratch/
brain/
.DS_Store
node_modules
```

**Gap:** Root-level `feedback.db` is not covered by `backend/feedback.db` pattern.

**Gap:** `*.txt` blocks all `.txt` files but `backend/debug_raw.txt` is a text file that may exist. `docling_output.md` at root is not gitignored and likely a scratch artifact.

### C4. Root-Level `.py` File Classification

| File | Classification | Rationale |
|---|---|---|
| `bbox_test.py` | **SCRATCH** | One-off bounding box debugging |
| `download_diagram.py` | **SCRATCH** | Download utility, no production use |
| `extract_colors.py` | **SCRATCH** | CSS color extraction dev tool |
| `generate_samples.py` | **SCRATCH** | Sample doc generation, dev-only |
| `scratch_table_test.py` | **SCRATCH** | Name is self-describing |
| `test_docling_parser.py` | **TEST** | Should move to `backend/tests/` |
| `test_orchestrator.py` | **TEST** | Should move to `backend/tests/` |
| `test_phase2.py` | **TEST** | Should move to `backend/tests/` |
| `test_post.py` | **TEST** | HTTP endpoint smoke test, move to `backend/tests/` |

Additionally in `backend/`:

| File | Classification | Rationale |
|---|---|---|
| `debug_party21.py` | **SCRATCH** | One-off party parsing debug |
| `debug_section4.py` | **SCRATCH** | One-off section debug |
| `debug_section5.py` | **SCRATCH** | One-off section debug |
| `debug_sections.py` | **SCRATCH** | One-off section debug |
| `debug_text.py` | **SCRATCH** | One-off text debug |
| `debug_vehicles.py` | **SCRATCH** | One-off vehicle debug |
| `dump_markdown.py` | **SCRATCH** | Dev utility |
| `fix_officer_patterns.py` | **SCRATCH** | One-off pattern fix script |
| `generate_test_docs.py` | **SCRATCH** | Doc generation utility |
| `test_all_states.py` | **TEST** | Move to `backend/tests/` |
| `test_extraction.py` | **TEST** | Move to `backend/tests/` — hardcoded path to `Downloads/crash_reports_sample_set` |
| `test_regression.py` | **TEST → PRODUCTION TEST** | 79 assertions, all passing; the only real test suite |
| `test_sample_set.py` | **TEST** | Move to `backend/tests/` |
| `train_feedback.py` | **PRODUCTION** | HITL training loop, wired into `main.py` |

---

## Section D: Test State

### D1. Test Quality

**`backend/test_regression.py`** — 79 real assertions using a `check()` helper. Current run: **79/79 passed (100%)**. Covers: module imports, form classifier (37 state cases), template merge, lookups API (NAIC, MMUCC, state codes), and end-to-end extraction on 6 synthetic text fixtures.

All other `test_*.py` files (root-level and others) are **print-debug scripts** with no assertions. They print output to stdout but will always exit 0 regardless of extraction quality.

### D2. CI Configuration

**No CI configured.** No `.github/workflows/` directory exists in the repository. No GitHub Actions, GitLab CI, or any other pipeline definition files were found.

### D3. Accuracy Benchmark

**No accuracy benchmark against real documents exists.** 

The `/api/benchmark/run` endpoint (`main.py:736–767`) measures regex throughput on a hardcoded 5-line mock string — it measures latency, not extraction accuracy.

`test_regression.py` uses synthetic text fixtures crafted to match the templates, which tests pipeline wiring but not generalization to real-world police report layouts.

No F1 scores, no field hit rates, no ground-truth corpus comparison is present anywhere in the repo.

---

## Section E: Template Engine + Extraction Logic

### E1. Template Inventory

**`backend/templates/police_report.json`** — base template for all police reports  
15 fields | Strategies: `global_regex` (scalars), `advanced_table` (arrays)

| Field ID | Strategy | Notes |
|---|---|---|
| `date_time` | global_regex | 9 patterns covering all major state label variants |
| `location` | global_regex | 8 patterns |
| `weather` | global_regex | 3 patterns |
| `road_surface` | global_regex | 2 patterns |
| `light_condition` | global_regex | 2 patterns |
| `accident_type` | global_regex | 9 patterns including checkbox, narrative, and crime type |
| `agency` | global_regex | 5 patterns |
| `officer` | global_regex | 7 patterns |
| `report_number` | global_regex | 6 patterns |
| `ems_agency` | global_regex | 5 patterns |
| `contributing_factors` | global_regex | 5 patterns |
| `property_damage` | global_regex | 3 patterns |
| `vehicles` | advanced_table | Vehicle table parser |
| `parties` | advanced_table | Operator/passenger table parser |
| `witnesses` | advanced_table | Witness table parser |

**`backend/templates/ia_report.json`** — Independent Adjuster reports  
13 fields | Strategy: `global_regex` only (no table parsing)

| Field ID | Notes |
|---|---|
| `cause_of_loss` | 4 patterns |
| `inspection_date` | 2 patterns |
| `inspection_firm` | 4 patterns |
| `coverage_a/b/c/d` | 2 patterns each |
| `coverages` | 2 patterns (policy form) |
| `officials` | 3 patterns |
| `subrogation` | 3 patterns |
| `settlement` | 5 patterns |
| `payment_summary` | 1 pattern |
| `recommendations` | 2 patterns (DOTALL) |

**`backend/templates/acord_report.json`** — ACORD submissions  
**0 fields** — empty `"fields": []` array. ACORD extraction uses `modules/acord_extractor.py` (hardcoded module), not the template engine. The orchestrator runs as a second pass for dynamic custom fields only.

**State overlay templates** — 51 state-specific JSON files (e.g., `tx_cr3.json`, `ca_chp555.json`). Each overrides or extends base `police_report.json` fields with state-specific patterns (e.g., checkbox_grid strategy for TX weather checkboxes). Template merge logic: `orchestrator_integration.py:_merge_templates()`.

### E2. State Form Classifier

**Yes, a full state classifier exists at `backend/core/form_classifier.py`.** It uses deterministic regex fingerprints (no ML) against the first 3,000 characters of the document. 51 state forms covered, each with 2–5 patterns (form number AND agency name, either sufficient).

Routing: `orchestrator_integration.py:_FORM_TEMPLATE_MAP` maps `form_id → state_json_filename`. When a form is classified as `tx_cr3`, the TX-specific template overlays the base `police_report.json`. When nothing matches, `generic_mmucc` falls through and only the base template runs.

**Known gap:** Both `sample_full_report.pdf` and `sample_21_fog_5veh_houston.pdf` (both Fort Worth / Houston TX reports) are classified as `generic_mmucc` (confidence 0.40). The TX form number or "TEXAS PEACE OFFICER" fingerprints are not appearing in the first 3,000 characters of these documents, so they miss the `tx_cr3` overlay.

### E3. Candidate Pool and Duplicate Detection

**Candidate gathering:** `backend/core/orchestrator.py:extract()` lines 61–67 — iterates all strategies for each field, calls `strat.run()`, appends all returned `Candidate` objects to `cands_per_field[field_id]`.

**Best candidate selection:** `backend/core/orchestrator.py:91` — `chosen = best(cands)` from `core/candidate.py:best()`.

**Duplicate insight generation:** `backend/main.py:237–248` — after orchestration, groups candidates by field_id; any field with >1 candidate produces a `duplicate_insights` entry in the API response.

### E4. HITL Alias Learning

**Implementation:** `backend/train_feedback.py:train_aliases()` and `learn_scalar_patterns()`.  
**Trigger:** `backend/main.py:646–663` — background thread spawned after every `POST /api/feedback/correction`.

**CRITICAL GAP — Aliases are learned but never applied:**

`train_aliases()` writes to `table_aliases` in `feedback.db`. The lookup function `database.py:get_aliases_for()` exists (lines 141–150) but is **never called** anywhere in the extraction pipeline. `advanced_table.py` uses a hardcoded `aliases` dict and never consults the database. `get_aliases_for()` has exactly one location in the entire codebase — its definition. The alias learning loop is broken: the write side works, the read side is wired to nothing.

### E5. IA Report Pipeline

**Yes, `ia_report.json` template exists.** The pipeline extracts 13 fields using `global_regex` strategies.

**Summary generation:** Hardcoded string concatenation in `backend/main.py:_format_ia_sentences()` (lines 67–128). The function assembles a prose paragraph from individual extracted fields using f-strings and `" ".join(sentences)`. No Jinja2, no template engine — pure Python string formatting.

---

## Section F: Known Extraction Failures

### F1. Pipeline Results on Sample Documents

**`sample_full_report.pdf`** (Fort Worth PD, 9 pages)
- Detected form: `generic_mmucc` (0.40 conf) — should be `tx_cr3`
- Fields extracted: 8/15 — weather, accident_type, agency, officer, contributing_factors, property_damage, vehicles, parties
- Fields missing: `date_time`, `location`, `road_surface`, `light_condition`, `report_number`, `ems_agency`, `witnesses`
- Confidence: all extracted fields at 0.6195 (below auto-accept threshold → **all** trigger `review_flags`)
- review_flags: every single extracted field flagged

**`sample_21_fog_5veh_houston.pdf`** (Houston PD, 5 pages)
- Detected form: `generic_mmucc` (0.40 conf) — should be `tx_cr3`
- Fields extracted: 10/15 — weather, light_condition, accident_type, agency, officer, ems_agency, property_damage, vehicles, parties, witnesses
- Fields missing: `date_time`, `location`, `road_surface`, `report_number`, `contributing_factors`
- Confidence: all at 0.6195 → all trigger review_flags

**`Police_Report_High_Complexity.pdf`** (synthetic, 1 page, 636 chars)
- Detected form: `generic_mmucc` (0.40 conf)
- Fields extracted: 6/15 — date_time, location, weather, accident_type, ems_agency, vehicles
- Fields missing: road_surface, light_condition, agency, officer, report_number, contributing_factors, property_damage, parties, witnesses
- Confidence: all at 0.6195

### F2. Failure Classification

| Field/Failure | Document | Layer | Root Cause |
|---|---|---|---|
| `date_time` = None | sample_full_report, sample_21 | **TEMPLATE_LAYER** | Label format in these TX reports ("SECTION 1 — CRASH DATE/TIME" without colon, or packed into a compound line) doesn't match any of the 9 regex patterns |
| `location` = None | sample_full_report, sample_21 | **TEMPLATE_LAYER** | Location appears in section headers ("SECTION 1 — CRASH LOCATION: I-45...") but the regex anchors require labels at line start |
| `report_number` = None | sample_full_report, sample_21 | **TEMPLATE_LAYER** | Report number format in these documents (e.g., "REPORT: FWPD-2024-XXXXX") doesn't match the report_number regex patterns |
| `form_id = generic_mmucc` (TX docs misclassified) | sample_full_report, sample_21 | **PARSE_LAYER** | TX fingerprints ("TEXAS PEACE OFFICER", "FORM CR-3") don't appear in first 3,000 characters of these documents; classifier scan window too narrow |
| All confidence = 0.6195 → all `review_flags` raised | all | **LAYOUT_LAYER** | Confidence scoring: global_regex base confidence is 1.0, but the generic_mmucc fallback path does not receive the state-specific scoring bonuses that state templates apply; combined with low validator pass-through, final score lands at 0.6195 for all fields |
| `witnesses` = None | sample_full_report | **TEMPLATE_LAYER** | Witness section in this document uses numbered table format (`1 Name Address Phone Statement`) which advanced_table.py's witness parser handles; may be failing due to pdfplumber column-reflow in the witness table |
| `acord_report.json` fields empty | ACORD docs | **TEMPLATE_LAYER** | Template has no fields; extraction entirely depends on hardcoded `acord_extractor.py` module which is not visible to the orchestrator audit trail |

---

## Section G: Dependencies

### G1. Backend Dependencies (`backend/requirements.txt`)

| Package | Version | License | Origin |
|---|---|---|---|
| `fastapi` | 0.115.5 | MIT | US (Sebastián Ramírez) |
| `uvicorn[standard]` | 0.32.1 | BSD-3-Clause | US (Encode) |
| `python-multipart` | 0.0.12 | Apache 2.0 | US |
| `pydantic` | 2.10.3 | MIT | US |
| `docling` | 2.15.0 | MIT | US (IBM Research) |
| `pdfplumber` | 0.11.9 | MIT | US (Jeremy Singer-Vine) |
| `spacy` | 3.8.14 | MIT | US (Explosion AI) |
| `en-core-web-lg` | 3.8.0 | MIT | US (Explosion AI) |

**Transitive deps of note** (not in requirements.txt but pulled in by docling):
- `easyocr` — Apache 2.0; author is Thai (JaidedAI); model weights hosted on GitHub
- `torch` / `torchvision` — BSD; Meta (US)
- `transformers` — Apache 2.0; Hugging Face (US)

### G2. Frontend Dependencies (`frontend/package.json`, top-level only)

**dependencies:**
| Package | Version | License |
|---|---|---|
| `@react-pdf-viewer/core` | ^3.12.0 | MIT |
| `@react-pdf-viewer/search` | ^3.12.0 | MIT |
| `lucide-react` | ^1.14.0 | ISC |
| `pdfjs-dist` | ^3.4.120 | Apache 2.0 (Mozilla) |
| `react` | ^19.2.5 | MIT (Meta) |
| `react-dom` | ^19.2.5 | MIT (Meta) |
| `react-pdf` | ^9.1.0 | MIT |

**devDependencies:**
| Package | License |
|---|---|
| `@eslint/js`, `eslint`, `eslint-plugin-*` | MIT |
| `@types/react`, `@types/react-dom` | MIT |
| `@vitejs/plugin-react`, `vite` | MIT |
| `globals` | MIT |

### G3. Flags

**No AGPL, GPL, or PRC-origin packages identified** in direct dependencies.

Items worth monitoring:
- `easyocr` (transitive via docling) — JaidedAI, Thailand-registered. Apache 2.0 license is clean, but data residency / model provenance should be reviewed for Posture B carriers.
- `torch` (transitive) — BSD license; Meta. Large binary (~2GB) pulled at install time; container image size concern for deployment.
- `docling_output.md` at repo root is not gitignored — if it contains PII from test documents, it should be added to `.gitignore`.

---

## Summary: Top Issues by Priority

| # | Issue | Section | Impact |
|---|---|---|---|
| 1 | HITL alias learning is broken — aliases stored but never read by extractors | E4 | High — feature described in README does not work end-to-end |
| 2 | Root `feedback.db` tracked by git | C1 | High — leaks DB state; should be gitignored |
| 3 | `date_time` and `location` missing on all TX sample docs | F1/F2 | High — core fields not extracted on primary document type |
| 4 | All extracted fields flagged as `review_flags` (0.6195 conf) | F1/F2 | High — review flag loses meaning if it fires on every field |
| 5 | TX form classifier not matching sample TX reports | F2 | Medium — falls back to generic_mmucc, misses TX-specific patterns |
| 6 | `acord_report.json` has empty fields array | E1 | Medium — ACORD template appears wired but does nothing |
| 7 | README claims RapidOCR, React 18, 100% extraction, spatial_label in use | B1–B3 | Medium — documentation misleads future developers and clients |
| 8 | No CI, no real-document accuracy benchmark | D2/D3 | Medium — regressions undetected; no objective accuracy measurement |
| 9 | 13 scratch/debug scripts in repo root and backend/ | C4 | Low — repo hygiene; confusing for contributors |
| 10 | Two `feedback.db` files (root orphan vs backend active) | C1/C2 | Low — confusion, wasted disk, git bloat |
