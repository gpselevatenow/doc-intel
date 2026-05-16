from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pdfplumber
import os
import re
import shutil
import time
import sqlite3
import asyncio
import json
import traceback
import threading

from core.parser import parse_document, flatten_markdown_tables, normalize_label_value_blocks, find_bbox_for_text, split_narrative_section
from core.ner_fallback import ner_fill_unknowns
from core.field_validator import validate_record
from core.confidence import score_record
from core.acroform import fill_hsmv_checkboxes
from core.form_classifier import classify_form, state_from_form_id
from core.code_decoder import decode_record
from modules.acord_extractor import extract_acord_report
from modules.hsmv_extractor import extract_hsmv_report
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
        "witnesses": [],
        "contributing_factors": "Unknown",
        "property_damage": "Unknown",
    }


def _na_if_none(val, fallback="N/A"):
    """Return fallback string when a field was not extracted."""
    if val is None or str(val).strip() == "":
        return fallback
    return val


def _check_reserve_warning(text: str) -> tuple:
    """Return (True, sentence) if the document contains reserve language, else (False, None)."""
    match = re.search(r'[^.!?\n]*\breserve\b[^.!?\n]*[.!?]?', text, re.IGNORECASE)
    if match:
        return True, match.group(0).strip()
    return False, None


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


def _format_police_narrative(record: dict, vehicles: list, parties: list, witnesses: list) -> str:
    """
    Convert police report extracted fields into a plain narrative paragraph.
    Used as the File Note for police and HSMV reports.
    """
    sentences = []

    accident_type = _na_if_none(record.get("accident_type"), "an unspecified type of collision")
    date_time = _na_if_none(record.get("date_time"), "an unknown date and time")
    location = _na_if_none(record.get("location"), "an unknown location")
    sentences.append(f"A {accident_type} collision occurred on {date_time} at {location}.")

    weather = record.get("weather")
    if weather and str(weather).strip().lower() not in ("", "unknown", "n/a"):
        sentences.append(f"Weather conditions were reported as {weather}.")

    agency = _na_if_none(record.get("agency"), "the responding agency")
    officer = _na_if_none(record.get("officer"), "an unidentified officer")
    sentences.append(f"The incident was investigated by {agency}, reporting officer {officer}.")

    report_number = record.get("report_number")
    if report_number and str(report_number).strip().lower() not in ("", "unknown", "n/a"):
        sentences.append(f"Report number: {report_number}.")

    ems = record.get("ems_agency")
    if ems and str(ems).strip().lower() not in ("", "unknown", "n/a"):
        sentences.append(f"EMS responded; agency: {ems}.")

    if vehicles:
        v_count = len(vehicles)
        sentences.append(
            f"A total of {v_count} vehicle{'s were' if v_count != 1 else ' was'} involved."
        )

    if parties:
        operators = [p for p in parties if p.get("role", "").lower() in ("operator", "driver")]
        injured = [
            p for p in parties
            if str(p.get("injuries", "None reported")).lower()
            not in ("none reported", "unknown", "", "n/a")
        ]
        if operators:
            n = len(operators)
            sentences.append(f"{n} operator{'s were' if n != 1 else ' was'} identified.")
        if injured:
            n = len(injured)
            sentences.append(f"{n} {'parties' if n != 1 else 'party'} reported injuries.")

    if witnesses:
        n = len(witnesses)
        sentences.append(f"{n} witness{'es were' if n != 1 else ' was'} identified at the scene.")

    cf = record.get("contributing_factors")
    if cf and str(cf).strip().lower() not in ("", "unknown", "n/a"):
        sentences.append(f"Contributing factors noted: {cf}.")

    pd = record.get("property_damage")
    if pd and str(pd).strip().lower() not in ("", "unknown", "n/a"):
        sentences.append(f"Non-vehicle property damage reported: {pd}.")

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

        reserve_warning, reserve_sentence = _check_reserve_warning(markdown_text)

        normalized = normalize_label_value_blocks(markdown_text)
        full_tables = flatten_markdown_tables(normalized)
        pre_narrative, _ = split_narrative_section(normalized)
        full_text = normalized + "\n\n" + full_tables

        if canonical_doc:
            canonical_doc.markdown = pre_narrative + "\n\n" + full_tables
            save_raw_document(file.filename, full_text)

            orchestrator_output = run_orchestrator(canonical_doc, file.filename, "ia_report")
            orchestrator_record = orchestrator_output["record"]
            orchestrator_record = ner_fill_unknowns(full_text, orchestrator_record, doc_type="ia")
            orchestrator_record = validate_record(orchestrator_record, doc_type="ia")
            review_flags = orchestrator_output["review_flags"]
            all_candidates = orchestrator_output.get("all_candidates", [])
            accuracy_score, field_scores, accuracy_reasons = score_record(
                orchestrator_record, doc_type="ia", all_candidates=all_candidates
            )

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
                "accuracy_score": accuracy_score,
                "accuracy_reasons": accuracy_reasons,
                "accuracy_field_scores": field_scores,
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
                "reserve_sentence": reserve_sentence,
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
            for i, vehicle in enumerate(result.get("vehicles", []) or []):
                for sub_field in ["vin", "plate", "owner_name", "owner_address",
                                   "insurance_company", "policy_number", "damages"]:
                    val = vehicle.get(sub_field)
                    if val and val not in ("Unknown", "N/A", "", None):
                        try:
                            hit = find_bbox_for_text(canonical_doc, str(val))
                            if hit:
                                bbox_map[f"vehicles[{i}].{sub_field}"] = hit
                        except Exception:
                            pass
            for role in ["operators", "passengers", "pedestrians"]:
                for i, party in enumerate(result.get(role, []) or []):
                    for sub_field in ["name", "dob", "address", "license_number"]:
                        val = party.get(sub_field) if isinstance(party, dict) else None
                        if val and val not in ("Unknown", "N/A", "", None) \
                                and len(str(val)) >= 3:
                            try:
                                hit = find_bbox_for_text(canonical_doc, str(val))
                                if hit:
                                    bbox_map[f"{role}[{i}].{sub_field}"] = hit
                            except Exception:
                                pass
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

        normalized = normalize_label_value_blocks(markdown_text)
        full_tables = flatten_markdown_tables(normalized)
        pre_narrative, _ = split_narrative_section(normalized)
        full_text = normalized + "\n\n" + full_tables

        if canonical_doc:
            # advanced_table was built against pdfplumber raw text, not Docling markdown.
            # Docling renders vehicle sections as tables; flatten_markdown_tables loses the
            # UNIT/VEHICLE #N section boundaries that advanced_table needs to split V1/V2/V3.
            # Use pdfplumber text as the canonical markdown for orchestrator extraction.
            import pdfplumber as _plumber
            _plumber_parts = []
            with _plumber.open(file_path) as _pdf:
                for _pg in _pdf.pages:
                    _plumber_parts.append(_pg.extract_text() or '')
            canonical_doc.markdown = '\n'.join(_plumber_parts)

            save_raw_document(file.filename, full_text)

            # Classify using pdfplumber text — classifier fingerprints were built on it
            form_id, form_confidence = classify_form('\n'.join(_plumber_parts))

            orchestrator_output = run_orchestrator(
                canonical_doc, file.filename, "police_report", form_id=form_id
            )
            orchestrator_record = orchestrator_output["record"]

            # NER fallback — use "hsmv" doc_type for FL forms, "police" for all others
            ner_doc_type = "hsmv" if form_id == "fl_hsmv" else "police"
            orchestrator_record = ner_fill_unknowns(pre_narrative, orchestrator_record, doc_type=ner_doc_type)

            # Decode numeric/alpha state-specific codes to human-readable values
            orchestrator_record = decode_record(orchestrator_record, form_id)

            orchestrator_record = validate_record(orchestrator_record, doc_type="police")
            review_flags = orchestrator_output["review_flags"]
            all_candidates = orchestrator_output.get("all_candidates", [])
            accuracy_score, field_scores, accuracy_reasons = score_record(
                orchestrator_record, doc_type="police", all_candidates=all_candidates
            )

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

            vehicles_list: list = []
            witnesses_list: list = []
            for key, target in [("vehicles", vehicles_list), ("witnesses", witnesses_list)]:
                try:
                    parsed = json.loads(orchestrator_record.get(key) or "[]")
                    target.extend(parsed)
                except Exception:
                    pass

            operators_list   = json.loads(orchestrator_record.get("operators")   or "[]")
            passengers_list  = json.loads(orchestrator_record.get("passengers")  or "[]")
            pedestrians_list = json.loads(orchestrator_record.get("pedestrians") or "[]")
            parties_list     = operators_list + passengers_list + pedestrians_list

            operators   = operators_list
            passengers  = passengers_list
            pedestrians = pedestrians_list
            for v in vehicles_list:
                if v.pop("_owner_same_as_driver", False) and operators:
                    v["owner_name"] = operators[0].get("name", v.get("owner_name", "Unknown"))
                    if v.get("owner_address", "Unknown") in ("Unknown", "", "Same as driver"):
                        v["owner_address"] = operators[0].get("address", "Unknown")

            narrative = _format_police_narrative(
                orchestrator_record, vehicles_list, parties_list, witnesses_list
            )

            result = {
                "accuracy_score": accuracy_score,
                "accuracy_reasons": accuracy_reasons,
                "accuracy_field_scores": field_scores,
                "summary": narrative,
                "form_id": form_id,
                "form_state": state_from_form_id(form_id),
                "form_confidence": round(form_confidence, 2),
                "date_time": _na_if_none(orchestrator_record.get("date_time"), "Unknown"),
                "location": _na_if_none(orchestrator_record.get("location"), "Unknown"),
                "weather": _na_if_none(orchestrator_record.get("weather"), "Unknown"),
                "accident_type": _na_if_none(orchestrator_record.get("accident_type"), "Unknown"),
                "agency": _na_if_none(orchestrator_record.get("agency"), "Unknown"),
                "officer": _na_if_none(orchestrator_record.get("officer"), "Unknown"),
                "report_number": _na_if_none(orchestrator_record.get("report_number"), "Unknown"),
                "ems_agency": _na_if_none(orchestrator_record.get("ems_agency"), "Unknown"),
                "contributing_factors": _na_if_none(orchestrator_record.get("contributing_factors"), "Unknown"),
                "property_damage": _na_if_none(orchestrator_record.get("property_damage"), "Unknown"),
                "light_condition": _na_if_none(orchestrator_record.get("light_condition")),
                "road_surface": _na_if_none(orchestrator_record.get("road_surface")),
                "vehicles": vehicles_list,
                "parties": parties_list,
                "operators": operators,
                "passengers": passengers,
                "pedestrians": pedestrians,
                "witnesses": witnesses_list,
                "dynamic_fields": {},
                "review_flags": review_flags,
                "duplicate_insights": duplicate_insights,
                "audit_trail": [c.to_dict() for c in all_candidates]
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
            for key, val in result.get("dynamic_fields", {}).items():
                if isinstance(val, str):
                    bbox_info = find_bbox_for_text(canonical_doc, val)
                    if bbox_info:
                        bbox_map[f"dynamic_{key}"] = bbox_info
            for i, vehicle in enumerate(result.get("vehicles", []) or []):
                for sub_field in ["vin", "plate", "owner_name", "owner_address",
                                   "insurance_company", "policy_number", "damages"]:
                    val = vehicle.get(sub_field)
                    if val and val not in ("Unknown", "N/A", "", None):
                        try:
                            hit = find_bbox_for_text(canonical_doc, str(val))
                            if hit:
                                bbox_map[f"vehicles[{i}].{sub_field}"] = hit
                        except Exception:
                            pass
            for role in ["operators", "passengers", "pedestrians"]:
                for i, party in enumerate(result.get(role, []) or []):
                    for sub_field in ["name", "dob", "address", "license_number"]:
                        val = party.get(sub_field) if isinstance(party, dict) else None
                        if val and val not in ("Unknown", "N/A", "", None) \
                                and len(str(val)) >= 3:
                            try:
                                hit = find_bbox_for_text(canonical_doc, str(val))
                                if hit:
                                    bbox_map[f"{role}[{i}].{sub_field}"] = hit
                            except Exception:
                                pass
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


@app.post("/api/extract/stream")
async def extract_stream(
    file: UploadFile = File(...),
    doc_type: str = Form("police_report")
):
    import tempfile, os, json as _json

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    async def generate():
        try:
            def emit(event: dict) -> str:
                return f"data: {_json.dumps(event)}\n\n"

            yield emit({"type": "step",
                "msg": "Reading document..."})
            await asyncio.sleep(0.05)

            text = ""
            with pdfplumber.open(tmp_path) as pdf:
                text = "\n".join(
                    p.extract_text() or ""
                    for p in pdf.pages)

            yield emit({"type": "step",
                "msg": "Classifying form..."})
            await asyncio.sleep(0.05)

            form_id, confidence = classify_form(text)
            yield emit({
                "type": "classified",
                "form_id": form_id,
                "confidence": round(confidence, 3),
                "msg": f"Classified as {form_id} ({round(confidence*100)}%)"
            })
            await asyncio.sleep(0.05)

            yield emit({"type": "step",
                "msg": "Extracting fields..."})
            await asyncio.sleep(0.05)

            markdown_text, canonical_doc = \
                parse_document(tmp_path)
            canonical_doc.markdown = text

            orchestrator_output = run_orchestrator(
                canonical_doc, file.filename,
                doc_type, form_id=form_id)
            record = orchestrator_output["record"]

            scalar_fields = [
                "date_time", "location", "weather",
                "road_surface", "light_condition",
                "accident_type", "agency", "officer",
                "report_number", "ems_agency",
                "contributing_factors",
                "property_damage", "cause_of_loss",
                "settlement", "subrogation",
                "coverage_a", "coverage_b",
                "coverage_c", "coverage_d",
                "inspection_date", "inspection_firm",
                "officials", "recommendations",
                "payment_summary"
            ]

            accuracy_scores = {}
            try:
                from backend.core.scoring import \
                    compute_accuracy_score
                accuracy_scores = \
                    compute_accuracy_score(record) or {}
            except:
                pass

            for field_id in scalar_fields:
                val = record.get(field_id)
                if val is None:
                    continue
                try:
                    parsed = _json.loads(val) \
                        if isinstance(val, str) \
                        and val.startswith('[') \
                        else val
                except:
                    parsed = val

                conf = accuracy_scores.get(
                    field_id, 0.85)

                yield emit({
                    "type": "field",
                    "field_id": field_id,
                    "value": str(parsed)[:120],
                    "confidence": round(
                        float(conf), 3),
                    "schema": {
                        "type": "currency"
                            if field_id in [
                                "settlement",
                                "coverage_a",
                                "coverage_b",
                                "coverage_c",
                                "coverage_d"]
                            else "date"
                            if "date" in field_id
                            else "text",
                        "label": field_id.replace(
                            "_", " ").title()
                    }
                })
                await asyncio.sleep(0.08)

            reserve_warning = bool(
                record.get("reserve_warning") or
                (record.get("settlement") and
                 "reserve" in str(
                    record.get("settlement", "")
                 ).lower()))

            if reserve_warning:
                yield emit({
                    "type": "flag",
                    "flag": "reserve",
                    "msg": "Reserve language detected"
                })
                await asyncio.sleep(0.05)

            vehicles = []
            try:
                v = record.get("vehicles")
                if v:
                    vehicles = _json.loads(v) \
                        if isinstance(v, str) else v
            except:
                pass

            if vehicles:
                yield emit({
                    "type": "vehicles",
                    "data": vehicles[:5]
                })
                await asyncio.sleep(0.05)

            parties = []
            for key in ["operators", "passengers",
                        "pedestrians"]:
                try:
                    p = record.get(key)
                    if p:
                        parsed_p = _json.loads(p) \
                            if isinstance(p, str) \
                            else p
                        parties.extend(parsed_p)
                except:
                    pass

            if parties:
                yield emit({
                    "type": "parties",
                    "data": parties[:10]
                })
                await asyncio.sleep(0.05)

            risk_score = 0
            if reserve_warning: risk_score += 3
            if "investig" in str(
                record.get("subrogation", "")
            ).lower(): risk_score += 2
            if len(vehicles) >= 3: risk_score += 1
            if len(parties) >= 3: risk_score += 1
            risk_level = "high" if risk_score >= 5 \
                else "medium" if risk_score >= 2 \
                else "low"

            yield emit({
                "type": "done",
                "risk_level": risk_level,
                "form_id": form_id,
                "field_count": len(scalar_fields),
                "msg": "Extraction complete"
            })

        except Exception as e:
            yield f"data: {_json.dumps({'type': 'error', 'msg': str(e)})}\n\n"
        finally:
            try: os.unlink(tmp_path)
            except: pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


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

        markdown_text = normalize_label_value_blocks(markdown_text)
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


@app.post("/api/extract/hsmv-report")
async def extract_hsmv(file: UploadFile = File(...)):
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

        normalized = normalize_label_value_blocks(markdown_text)
        full_tables = flatten_markdown_tables(normalized)
        pre_narrative, _ = split_narrative_section(normalized)
        full_text = normalized + "\n\n" + full_tables

        if canonical_doc:
            canonical_doc.markdown = pre_narrative + "\n\n" + full_tables
            save_raw_document(file.filename, full_text)

        hsmv_data = extract_hsmv_report(full_text)
        hsmv_data = fill_hsmv_checkboxes(file_path, hsmv_data)
        hsmv_data = ner_fill_unknowns(pre_narrative, hsmv_data, doc_type="hsmv")
        hsmv_data = validate_record(hsmv_data, doc_type="hsmv")

        # Run police_report orchestrator as a secondary pass to fill Unknown fields
        review_flags = {}
        all_candidates = []
        if canonical_doc:
            try:
                orchestrator_output = run_orchestrator(canonical_doc, file.filename, "police_report")
                orch_record = orchestrator_output["record"]
                review_flags = orchestrator_output["review_flags"]
                all_candidates = orchestrator_output.get("all_candidates", [])
                for field in ("date_time", "location", "weather", "accident_type",
                              "agency", "officer", "report_number", "ems_agency"):
                    if hsmv_data.get(field, "Unknown") == "Unknown":
                        orch_val = orch_record.get(field)
                        if orch_val and str(orch_val).strip() not in ("", "Unknown"):
                            hsmv_data[field] = orch_val
            except Exception:
                pass

        accuracy_score, field_scores, accuracy_reasons = score_record(
            hsmv_data, doc_type="hsmv", all_candidates=all_candidates
        )

        result = {
            "accuracy_score": accuracy_score,
            "accuracy_reasons": accuracy_reasons,
            "accuracy_field_scores": field_scores,
            "summary": "Florida HSMV 90010S Traffic Crash Report extracted.",
            "date_time": _na_if_none(hsmv_data.get("date_time"), "Unknown"),
            "location": _na_if_none(hsmv_data.get("location"), "Unknown"),
            "weather": _na_if_none(hsmv_data.get("weather"), "Unknown"),
            "accident_type": _na_if_none(hsmv_data.get("accident_type"), "Unknown"),
            "agency": _na_if_none(hsmv_data.get("agency"), "Unknown"),
            "officer": _na_if_none(hsmv_data.get("officer"), "Unknown"),
            "report_number": _na_if_none(hsmv_data.get("report_number"), "Unknown"),
            "ems_agency": _na_if_none(hsmv_data.get("ems_agency"), "Unknown"),
            "dynamic_fields": {},
            "review_flags": review_flags,
            "duplicate_insights": [],
            "audit_trail": [c.to_dict() for c in all_candidates],
            "vehicles": hsmv_data.get("vehicles", []),
            "parties": hsmv_data.get("parties", []),
            "witnesses": hsmv_data.get("witnesses", []),
        }

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
        print(f"Exception in extract_hsmv: {traceback.format_exc()}")
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

def _bg_train():
    try:
        from train_feedback import run_all_training
        run_all_training()
    except Exception as e:
        print(f"Background training error: {e}")


@app.post("/api/feedback/correction")
async def receive_correction(correction: CorrectionModel):
    try:
        log_correction(
            doc_id=correction.doc_id,
            field_name=correction.field_name,
            original_value=correction.original_value,
            new_value=correction.new_value
        )
        threading.Thread(target=_bg_train, daemon=True).start()
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


@app.get("/api/benchmark/failures")
async def benchmark_failures():
    """Top corrected fields and recent corrections from feedback.db."""
    from database import DB_NAME
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT field_name, COUNT(*) as cnt
            FROM corrections
            GROUP BY field_name
            ORDER BY cnt DESC
            LIMIT 10
        """)
        top_failures = [{"field": row[0], "correction_count": row[1]} for row in cursor.fetchall()]
        cursor.execute("""
            SELECT doc_id, field_name, original_value, new_value, timestamp
            FROM corrections
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        recent = [
            {"doc_id": r[0], "field": r[1], "from": r[2], "to": r[3], "at": r[4]}
            for r in cursor.fetchall()
        ]
        conn.close()
        return {
            "status": "success",
            "top_failures": top_failures,
            "recent_corrections": recent,
            "total_corrections": sum(f["correction_count"] for f in top_failures),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    uvicorn.run(app, host="0.0.0.0", port=8002)
