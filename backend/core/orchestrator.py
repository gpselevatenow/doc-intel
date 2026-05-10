"""Orchestrator â€” Layer 7.

Pipeline:
    FOR EACH FIELD in template:
        FOR EACH STRATEGY in field.strategies (ordered by priority):
            run strategy â†’ list of Candidates
        merge candidates (across strategies) for the field
        validate all candidates against the field's validators
        score every candidate (rejected â†’ 0)
        pick the highest-scoring non-rejected candidate
        emit audit entry with full provenance + score breakdown
    return record + audit + summary stats

Returns a plain dict so the caller can hand it directly to the
ExtractionRunDoc Beanie wrapper without further marshalling.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import asdict
from typing import Any

from core.candidate import Candidate, best
from core.document_model import Document
from core.scoring import score_candidate
from core.template_schema import TemplateSchema
from core.validation import validate_all
from extractors.base import STRATEGY_REGISTRY


def _instantiate_strategy(name: str):
    cls = STRATEGY_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"strategy not registered: {name!r}")
    return cls()


def extract(
    document: Document,
    template: TemplateSchema,
    *,
    low_confidence_threshold: float | None = None,
) -> dict[str, Any]:
    """Run every strategy for every field, validate, score, pick best.

    Returns:
        {
          "record":        flat dict[field_id, value-or-None],
          "audit":         list of per-field audit entries,
          "summary_stats": counts + timing,
          "all_candidates": list of every Candidate produced (for diagnostics),
        }
    """
    t0 = time.perf_counter()
    threshold = (low_confidence_threshold
                 if low_confidence_threshold is not None
                 else template.auto_accept_threshold)

    # 1) Generate candidates
    cands_per_field: dict[str, list[Candidate]] = defaultdict(list)
    for fdef in template.fields:
        for entry in sorted(fdef.strategies, key=lambda s: s.priority):
            strat = _instantiate_strategy(entry.strategy)
            for c in strat.run(document, fdef.field_id, entry.config):
                c.strategy_priority = entry.priority
                cands_per_field[fdef.field_id].append(c)

    # 2) Validate
    rules_by_field = {f.field_id: f.validators for f in template.fields}
    validate_all(cands_per_field, rules_by_field)

    # 3) Score
    for fdef in template.fields:
        n_validators = len(fdef.validators)
        for c in cands_per_field.get(fdef.field_id, []):
            score_candidate(c, n_validators)

    # 4) Select best + audit
    record:           dict[str, Any]       = {}
    audit:            list[dict[str, Any]] = []
    confidences:      list[float]          = []
    all_candidates:   list[Candidate]      = []
    n_extracted = 0
    n_low_conf  = 0

    for fdef in template.fields:
        cands = cands_per_field.get(fdef.field_id, [])
        all_candidates.extend(cands)
        rejected_count = sum(1 for c in cands if c.rejected)
        chosen = best(cands)

        if chosen is None:
            record[fdef.field_id] = None
            audit.append({
                "field_id":              fdef.field_id,
                "value":                 None,
                "confidence":            0.0,
                "candidates_considered": len(cands),
                "rejected_count":        rejected_count,
                "needs_review":          fdef.required,
            })
            continue

        record[fdef.field_id] = chosen.value
        confidences.append(chosen.confidence)
        n_extracted += 1
        needs_review = chosen.confidence < threshold
        if needs_review:
            n_low_conf += 1

        audit.append({
            "field_id":              fdef.field_id,
            "value":                 chosen.value,
            "confidence":            round(chosen.confidence, 4),
            "source_strategy":       chosen.source_strategy,
            "page":                  chosen.page,
            "bbox":                  chosen.bbox,
            "label_text":            chosen.label_text,
            "label_bbox":            chosen.label_bbox,
            "raw_match_text":        chosen.raw_match_text,
            "match_pattern":         chosen.match_pattern,
            "score_breakdown":       {k: round(v, 4) for k, v in asdict(chosen.score).items()},
            "validators_passed":     [v.validator_type for v in chosen.validation_results if v.passed],
            "validators_failed":     [{"type": v.validator_type, "reason": v.reason}
                                       for v in chosen.validation_results if not v.passed],
            "candidates_considered": len(cands),
            "rejected_count":        rejected_count,
            "needs_review":          needs_review,
        })

    elapsed = time.perf_counter() - t0
    summary = {
        "fields_total":          len(template.fields),
        "fields_extracted":      n_extracted,
        "fields_low_confidence": n_low_conf,
        "avg_confidence":        round((sum(confidences) / len(confidences)) if confidences else 0.0, 4),
        "elapsed_seconds":       round(elapsed, 4),
        "has_low_confidence":    n_low_conf > 0,
    }

    return {
        "record":         record,
        "audit":          audit,
        "summary_stats":  summary,
        "all_candidates": all_candidates,
    }

