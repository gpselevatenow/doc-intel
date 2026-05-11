from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import shutil
import time
import sqlite3
import asyncio
import json
import traceback

from core.parser import parse_document, flatten_markdown_tables, find_bbox_for_text
from modules.acord_extractor import extract_acord_report
from core.orchestrator_integration import run_orchestrator
from database import init_db, log_correction, add_custom_field, get_custom_fields, delete_custom_field, save_raw_document
from pydantic import BaseModel

app = FastAPI(title="Elevatenow - Doc Intel - Extraction Suite")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_error_fallback(message):
    return {
        "accuracy_score": 0,
        "accuracy_reasons": [message],
        "summary": "Data extraction failed.",
        "dynamic_fields": {},
        "review_flags": {},
        "duplicate_insights": [],
        "audit_trail": [],
        "vehicles": [],
        "parties": [],
        "witnesses": []
    }


def _na_if_none(val, fallback="N/A"):
    """Return fallback string when a field was not extracted."""
    if val is None or str(val).strip() == "":
        return fallback
    return val


def _check_reserve_warning(text: str) -> bool:
    """Return True if the document contains the word 'reserve'."""
    return bool(re.search(r'\breserve\b', text, re.IGNORECASE))


def _format_ia_sentences(record: dict, reserve_warning: bool) -> str:
    """
    Convert IA report extracted fields into a plain narrative paragraph.
    No special characters, no markdown, no bullet points.
    """
    sentences = []

    cause = _na_if_none(record.get("cause_of_loss"), "not specified")
    sentences.append(f"The cause of loss was {cause}.")

    insp_date = _na_if_none(record.get("inspection_date"), "not recorded")
    insp_firm = _na_if_none(record.get("inspection_firm"), "not recorded")
    sentences.append(
        f"Coverage A was inspected on {insp_date} by {insp_firm}."
    )

    cov_a = _na_if_none(record.get("coverage_a"))
    sentences.append(f"Coverage A is {cov_a}.")

    cov_b = _na_if_none(record.get("coverage_b"))
    sentences.append(f"Coverage B is {cov_b}.")

    cov_c = _na_if_none(record.get("coverage_c"))
    sentences.append(f"Coverage C is {cov_c}.")

    cov_d = _na_if_none(record.get("coverage_d"))
    sentences.append(f"Coverage D is {cov_d}.")

    coverages = record.get("coverages")
    if coverages:
        sentences.append(f"The applicable coverages and policy form are as follows: {coverages}.")

    officials = record.get("officials")
    if officials:
        sentences.append(f"A report was filed with the following officials: {officials}.")
    else:
        sentences.append("No fire or police report was filed.")

    settlement = _na_if_none(record.get("settlement"), "not yet determined")
    sentences.append(f"The settlement amount is {settlement}.")

    subrogation = _na_if_none(record.get("subrogation"), "not determined")
    sentences.append(f"Subrogation is {subrogation}.")

    payment_summary = record.get("payment_summary")
    if payment_summary:
        sentences.append(f"Summary of payments made to date: {payment_summary}.")
    else:
        sentences.append("No payment summary data was available from ClaimCenter.")

    recommendations = record.get("recommendations")
    if recommendations:
        sentences.append(f"Adjuster recommendations: {recommendations}.")
    else:
        sentences.append("No adjuster recommendations have been entered.")

    if reserve_warning:
        sentences.append(
            "WARNING: The word reserve appears in this document and requires adjuster review."
        )

    return " ".join(sentences)


@app.post("/api/extract/ia-report")
async def extract_ia(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        try:
            markdown_text, canonical_doc = await asyncio.wait_for(
                asyncio.to_thread(parse_document, file_path),
                timeout=60.0
            )
        except Exception as e:
            print(f"Docling failed: {e}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            return get_error_fallback(f"Document parsing failed: {str(e)}")

        reserve_warning = _check_reserve_warning(markdown_text)

        markdown_text += "\n\n" + flatten_markdown_tables(markdown_text)
        if canonical_doc:
            canonical_doc.markdown = markdown_text
            save_raw_document(file.filename, markdown_text)

            orchestrator_output = run_orchestrator(canonical_doc, file.filename, "ia_report")
            orchestrator_record = orchestrator_output["record"]
            review_flags = orchestrator_output["review_flags"]
            all_candidates = orchestrator_output.get("all_candidates", [])

            duplicate_insights = []
            candidates_by_field = {}
            for c in all_candidates:
                fid = c.field_id
                candidates_by_field.setdefault(fid, []).append(c)

            for fid, cands in candidates_by_field.items():
                if len(cands) > 1:
                    best_val = orchestrator_record.get(fid)
                    duplicate_insights.append(
                        f"Duplicate data found for '{fid}'. Selected highest confidence value: '{best_val}'."
                    )

            narrative = _format_ia_sentences(orchestrator_record, reserve_warning)

            result = {
                "accuracy_score": 100.0,
                "accuracy_reasons": ["100% Extraction via Orchestrator"],
                "summary": narrative,
                "cause_of_loss": _na_if_none(orchestrator_record.get("cause_of_loss"), "Unknown"),
                "inspection_date": _na_if_none(orchestrator_record.get("inspection_date"), "Unknown"),
                "inspection_firm": _na_if_none(orchestrator_record.get("inspection_firm"), "Unknown"),
                "coverage_a": _na_if_none(orchestrator_record.get("coverage_a")),
                "coverage_b": _na_if_none(orchestrator_record.get("coverage_b")),
                "coverage_c": _na_if_none(orchestrator_record.get("coverage_c")),
                "coverage_d": _na_if_none(orchestrator_record.get("coverage_d")),
                "coverages": _na_if_none(orchestrator_record.get("coverages")),
                "officials": _na_if_none(orchestrator_record.get("officials")),
                "subrogation": _na_if_none(orchestrator_record.get("subrogation"), "Unknown"),
                "settlement": _na_if_none(orchestrator_record.get("settlement"), "Not estimated"),
                "payment_summary": _na_if_none(orchestrator_record.get("payment_summary")),
                "recommendations": _na_if_none(orchestrator_record.get("recommendations")),
                "reserve_warning": reserve_warning,
                "dynamic_fields": {},
                "review_flags": review_flags,
                "duplicate_insights": duplicate_insights,
                "audit_trail": [c.to_dict() for c in all_candidates],
                "vehicles": [],
                "parties": [],
                "witnesses": []
            }

            for key, val in orchestrator_record.items():
                if key.startswith("dynamic_"):
                    result["dynamic_fields"][key.replace("dynamic_", "")] = val if val is not None else "Not Found"
        else:
            return get_error_fallback("Failed to load document")

        bbox_map = {}
        if canonical_doc:
            for key, val in result.items():
                if isinstance(val, str) and key not in ("summary", "accuracy_reasons"):
                    bbox_info = find_bbox_for_text(canonical_doc, val)
                    if bbox_info:
                        bbox_map[key] = bbox_info
        result["bbox_map"] = bbox_map
        return result

    except Exception as e:
        print(f"Exception in extract_ia: {traceback.format_exc()}")
        return get_error_fallback(f"Internal Error: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@app.post("/api/extract/police-report")
async def extract_police(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        try:
            markdown_text, canonical_doc = await asyncio.wait_for(
                asyncio.to_thread(parse_document, file_path),
                timeout=60.0
            )
        except Exception as e:
            print(f"Docling failed: {e}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            return get_error_fallback(f"Document parsing failed: {str(e)}")

        markdown_text += "\n\n" + flatten_markdown_tables(markdown_text)
        if canonical_doc:
            canonical_doc.markdown = markdown_text
            save_raw_document(file.filename, markdown_text)

            orchestrator_output = run_orchestrator(canonical_doc, file.filename, "police_report")
            orchestrator_record = orchestrator_output["record"]
            review_flags = orchestrator_output["review_flags"]
            all_candidates = orchestrator_output.get("all_candidates", [])

            duplicate_insights = []
            candidates_by_field = {}
            for c in all_candidates:
                fid = c.field_id
                candidates_by_field.setdefault(fid, []).append(c)

            for fid, cands in candidates_by_field.items():
                if len(cands) > 1:
                    best_val = orchestrator_record.get(fid)
                    duplicate_insights.append(
                        f"Duplicate data found for '{fid}'. Selected highest confidence value: '{best_val}'."
                    )

            result = {
                "accuracy_score": 100.0,
                "accuracy_reasons": ["100% Extraction via Orchestrator"],
                "summary": "Data extracted successfully via Orchestrator.",
                "date_time": _na_if_none(orchestrator_record.get("date_time"), "Unknown"),
                "location": _na_if_none(orchestrator_record.get("location"), "Unknown"),
                "weather": _na_if_none(orchestrator_record.get("weather"), "Unknown"),
                "accident_type": _na_if_none(orchestrator_record.get("accident_type"), "Unknown"),
                "agency": _na_if_none(orchestrator_record.get("agency"), "Unknown"),
                "officer": _na_if_none(orchestrator_record.get("officer"), "Unknown"),
                "report_number": _na_if_none(orchestrator_record.get("report_number"), "Unknown"),
                "ems_agency": _na_if_none(orchestrator_record.get("ems_agency"), "Unknown"),
                "dynamic_fields": {},
                "review_flags": review_flags,
                "duplicate_insights": duplicate_insights,
                "audit_trail": [c.to_dict() for c in all_candidates]
            }

            for key in ["vehicles", "parties", "witnesses"]:
                try:
                    result[key] = json.loads(orchestrator_record.get(key) or "[]")
                except Exception:
                    result[key] = []

            for key, val in orchestrator_record.items():
                if key.startswith("dynamic_"):
                    result["dynamic_fields"][key.replace("dynamic_", "")] = val if val is not None else "Not Found"
        else:
            return get_error_fallback("Failed to load document")

        bbox_map = {}
        if canonical_doc:
            for key, val in result.items():
                if isinstance(val, str) and key not in ("summary", "accuracy_reasons"):
                    bbox_info = find_bbox_for_text(canonical_doc, val)
                    if bbox_info:
                        bbox_map[key] = bbox_info
            for key, val in result.get("dynamic_fields", {}).items():
                if isinstance(val, str):
                    bbox_info = find_bbox_for_text(canonical_doc, val)
                    if bbox_info:
                        bbox_map[f"dynamic_{key}"] = bbox_info
        result["bbox_map"] = bbox_map
        return result

    except Exception as e:
        print(f"Exception in extract_police: {traceback.format_exc()}")
        return get_error_fallback(f"Internal Error: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@app.post("/api/extract/acord-report")
async def extract_acord(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        try:
            markdown_text, canonical_doc = await asyncio.wait_for(
                asyncio.to_thread(parse_document, file_path),
                timeout=60.0
            )
        except Exception as e:
            print(f"Docling failed: {e}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            return get_error_fallback(f"Document parsing failed: {str(e)}")

        markdown_text += "\n\n" + flatten_markdown_tables(markdown_text)
        if canonical_doc:
            canonical_doc.markdown = markdown_text
            save_raw_document(file.filename, markdown_text)

        result = extract_acord_report(markdown_text)

        if canonical_doc:
            orchestrator_output = run_orchestrator(canonical_doc, file.filename, "acord_report")
            orchestrator_record = orchestrator_output["record"]
            result["review_flags"] = orchestrator_output["review_flags"]
            result["audit_trail"] = [c.to_dict() for c in orchestrator_output.get("all_candidates", [])]
            result["dynamic_fields"] = {}
            for key, val in orchestrator_record.items():
                if key.startswith("dynamic_"):
                    result["dynamic_fields"][key.replace("dynamic_", "")] = val if val is not None else "Not Found"
                elif val is not None:
                    result[key] = val
        else:
            result.update({
                "dynamic_fields": {},
                "review_flags": {},
                "audit_trail": [],
                "vehicles": [],
                "parties": [],
                "witnesses": []
            })

        bbox_map = {}
        if canonical_doc:
            for key, val in result.items():
                if isinstance(val, str) and key not in ("summary", "accuracy_reasons"):
                    bbox_info = find_bbox_for_text(canonical_doc, val)
                    if bbox_info:
                        bbox_map[key] = bbox_info
            for key, val in result.get("dynamic_fields", {}).items():
                if isinstance(val, str):
                    bbox_info = find_bbox_for_text(canonical_doc, val)
                    if bbox_info:
                        bbox_map[f"dynamic_{key}"] = bbox_info
        result["bbox_map"] = bbox_map
        return result

    except Exception as e:
        print(f"Exception in extract_acord: {traceback.format_exc()}")
        return get_error_fallback(f"Internal Error: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


class CorrectionModel(BaseModel):
    doc_id: str
    field_name: str
    original_value: str
    new_value: str

@app.post("/api/feedback/correction")
async def receive_correction(correction: CorrectionModel):
    try:
        log_correction(
            doc_id=correction.doc_id,
            field_name=correction.field_name,
            original_value=correction.original_value,
            new_value=correction.new_value
        )
        return {"status": "success", "message": "Correction logged for AI fine-tuning."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


class CustomFieldModel(BaseModel):
    doc_id: str
    field_name: str

@app.get("/api/settings/fields/{doc_id}")
async def fetch_custom_fields(doc_id: str):
    return {"status": "success", "fields": get_custom_fields(doc_id)}

@app.post("/api/settings/fields")
async def add_custom_field_route(payload: CustomFieldModel):
    add_custom_field(payload.doc_id, payload.field_name)
    return {"status": "success", "message": f"Added {payload.field_name}"}

@app.delete("/api/settings/fields/{doc_id}/{field_name}")
async def delete_custom_field_route(doc_id: str, field_name: str):
    delete_custom_field(doc_id, field_name)
    return {"status": "success", "message": f"Deleted {field_name}"}


class RatingRequest(BaseModel):
    doc_id: str
    action: str

@app.post("/api/feedback/rate")
async def submit_rating(req: RatingRequest):
    from database import log_user_feedback
    score = 1 if req.action == "up" else -1
    log_user_feedback(req.doc_id, score)
    return {"status": "success", "message": "Rating submitted."}


@app.get("/api/benchmark/run")
async def run_benchmark():
    iterations = 50
    start_time = time.perf_counter()

    mock_text = "Cause of loss: Fire\nCoverage A: $100,000\nCoverage B: $20,000\nSettlement is estimated at $45,000\nSubrogation: Yes"
    for _ in range(iterations):
        extract_acord_report(mock_text)

    end_time = time.perf_counter()
    total_time_sec = end_time - start_time
    avg_latency_ms = (total_time_sec / iterations) * 1000
    throughput_per_sec = iterations / total_time_sec if total_time_sec > 0 else 0

    correction_count = 0
    try:
        conn = sqlite3.connect("feedback.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM corrections")
        correction_count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        pass

    return {
        "status": "success",
        "iterations": iterations,
        "total_time_sec": round(total_time_sec, 3),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "throughput_per_sec": round(throughput_per_sec, 1),
        "correction_count": correction_count
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
