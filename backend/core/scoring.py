"""Scoring engine — Layer 5.

Each Candidate is scored from multiple signals, weighted and combined
into a final confidence in [0, 1]. The orchestrator then picks the
highest-scoring non-rejected Candidate per field.

Default signal weights:
    label_proximity        0.30
    validator_pass         0.25
    regex_confidence       0.15
    ocr_confidence         0.10
    page_preference        0.05
    region_alignment       0.05
    multiline_consistency  0.10
    overlap_penalty       -0.05  (subtracted)

Strategy priority is folded in as a small additive bonus (lower
priority number → larger bonus, capped at 0.05).

Rejected candidates score to 0.0 immediately.
"""
from __future__ import annotations

from backend.core.candidate import Candidate, ScoreBreakdown
from backend.extractors._geometry import aabb_overlap


WEIGHTS: dict[str, float] = {
    "label_proximity":       0.30,
    "validator_pass":        0.25,
    "regex_confidence":      0.15,
    "ocr_confidence":        0.10,
    "page_preference":       0.05,
    "region_alignment":      0.05,
    "multiline_consistency": 0.10,
    "overlap_penalty":      -0.05,
}


# ── Individual signals ──────────────────────────────────────────────

def _label_proximity(c: Candidate) -> float:
    """Closer label = higher signal. label_distance is set by spatial_label."""
    if c.bbox is None or c.label_bbox is None:
        return 0.0
    dist = c.metadata.get("label_distance")
    if dist is None:
        return 0.5     # have a label but distance not recorded — partial credit
    if dist <= 30:
        return 1.0
    if dist >= 200:
        return 0.0
    return 1.0 - ((dist - 30) / 170.0)


def _validator_pass(c: Candidate, num_validators: int) -> float:
    if num_validators == 0:
        return 1.0      # no validators declared → neutral pass
    if c.rejected:
        return 0.0
    passed = sum(1 for v in c.validation_results if v.passed)
    return passed / num_validators


def _regex_confidence(c: Candidate) -> float:
    """Boost candidates whose value was constrained by a regex (value_pattern or pure regex)."""
    return 1.0 if c.match_pattern else 0.5


def _ocr_confidence(c: Candidate) -> float:
    return c.ocr_confidence if c.ocr_confidence is not None else 0.7


def _page_preference(c: Candidate) -> float:
    """Forms tend to put structured fields on page 1 — slight bias."""
    if c.page is None:
        return 0.5
    return 1.0 if c.page == 1 else 0.7


def _region_alignment(c: Candidate) -> float:
    """Placeholder for anchor_region strategy. Neutral until that strategy lands."""
    return 0.5


def _multiline_consistency(c: Candidate) -> float:
    """Placeholder for multi-line value coherence checks. Neutral for now."""
    return 0.5


def _overlap_penalty(c: Candidate) -> float:
    """Penalty when value bbox overlaps the label bbox (suggests a bad pairing)."""
    if c.bbox is None or c.label_bbox is None:
        return 0.0
    return 1.0 if aabb_overlap(c.bbox, c.label_bbox) else 0.0


# ── Combine ─────────────────────────────────────────────────────────

def score_candidate(c: Candidate, num_validators: int) -> None:
    """Mutates c.score (breakdown) and c.confidence (final)."""
    if c.rejected:
        c.confidence = 0.0
        c.score.final = 0.0
        return

    sig = ScoreBreakdown(
        label_proximity       = _label_proximity(c),
        validator_pass        = _validator_pass(c, num_validators),
        regex_confidence      = _regex_confidence(c),
        ocr_confidence        = _ocr_confidence(c),
        page_preference       = _page_preference(c),
        region_alignment      = _region_alignment(c),
        multiline_consistency = _multiline_consistency(c),
        overlap_penalty       = _overlap_penalty(c),
    )

    score = (
        WEIGHTS["label_proximity"]       * sig.label_proximity
      + WEIGHTS["validator_pass"]        * sig.validator_pass
      + WEIGHTS["regex_confidence"]      * sig.regex_confidence
      + WEIGHTS["ocr_confidence"]        * sig.ocr_confidence
      + WEIGHTS["page_preference"]       * sig.page_preference
      + WEIGHTS["region_alignment"]      * sig.region_alignment
      + WEIGHTS["multiline_consistency"] * sig.multiline_consistency
      + WEIGHTS["overlap_penalty"]       * sig.overlap_penalty
    )

    # Strategy priority bonus — at most +0.05
    pri = max(0, c.strategy_priority)
    priority_bonus = min(0.05, max(0.0, (100 - pri) * 0.0005))
    score += priority_bonus

    sig.final = max(0.0, min(1.0, score))
    c.score = sig
    c.confidence = sig.final
