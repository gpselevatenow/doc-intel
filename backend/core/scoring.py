"""Scoring engine — Layer 5.

Each Candidate is scored from multiple signals, weighted and combined into a
final confidence in [0, 1]. The orchestrator picks the highest-scoring
non-rejected Candidate per field.

Docling path (bbox present): spatial signals are used directly.
pdfplumber path (bbox absent): text-based signals derived from match_span,
  the regex pattern itself, and the full document text.

── Components and what each measures ─────────────────────────────────────────

  label_proximity       — Did the match land close to its field label?
                          Docling: pixel distance between value bbox and label bbox.
                          pdfplumber: character distance from match_span[0] to the
                          nearest occurrence of any declared label_text term.

  validator_pass        — Fraction of declared template validators the value
                          satisfies. Syntactic gate (min/max length, pattern checks).
                          Rejected candidates score 0.0 immediately.

  regex_confidence      — Whether the value was captured by an explicit pattern
                          (1.0) or a fallback heuristic (0.5). Rewards specificity
                          in pattern design.

  ocr_confidence        — Docling: per-word OCR confidence from the layout engine.
                          pdfplumber: pattern specificity score normalised across the
                          field's candidate pool, mapped to [0.40, 1.00].

  page_preference       — Docling: page-1 bias (page 1 = 1.0, later pages = 0.7).
                          pdfplumber: relative position of the match in the document
                          vs. the field's declared expected_position ("header", "footer",
                          "any"). Neutral (0.5) when expected_position is not declared.

  region_alignment      — Docling: anchor-region spatial check (placeholder 0.5).
                          pdfplumber: multi-pattern agreement — how many non-rejected
                          candidates for this field agree on the same normalised value.
                          3+ agree → 1.0 / 2 agree → 0.85 / conflicting → 0.30.

  multiline_consistency — Docling: multi-line coherence (placeholder 0.5).
                          pdfplumber: semantic plausibility via PLAUSIBILITY_REGISTRY
                          in core/plausibility.py. Each registered field_id has a
                          bespoke function that checks whether the extracted value
                          makes sense for that field type (date ranges, VIN format,
                          road terminology, EMS vocabulary, etc.). Returns 0.5 for
                          fields with no registered check (neutral). Unregistered
                          fields are not penalised — only actively-bad values score low.

  overlap_penalty       — Docling only: penalises when the value bbox spatially
                          overlaps the label bbox (label text leaked into value).
                          Always 0.0 on the pdfplumber path (no spatial data).

── Weights and rationale ─────────────────────────────────────────────────────

Signal weights (positive weights sum to 1.00):

  label_proximity        0.15  — strong signal but also fires on garbage OCR near labels
  validator_pass         0.15  — syntactic gate; failures already reject the candidate
  regex_confidence       0.05  — reduced; nearly all production patterns carry a match
  ocr_confidence         0.10  — pattern specificity proxy on pdfplumber path
  page_preference        0.05  — weak position prior; most fields appear on page 1
  region_alignment       0.15  — multi-pattern agreement is the best structural signal
  multiline_consistency  0.35  — plausibility is the only component that measures whether
                                 the extracted value is semantically meaningful; up-weighted
                                 so that implausible values (score 0.2) meaningfully reduce
                                 confidence even when structural signals are strong
  overlap_penalty       -0.05  — bbox-overlap penalty (Docling only)

Rationale for up-weighting multiline_consistency (plausibility) to 0.35:
  Structural signals (label_proximity, regex_confidence, ocr_confidence) are
  satisfied by garbage OCR matches that land near a label with a well-formed
  pattern. Plausibility is the only component that independently validates the
  extracted value. At 0.20 (prior weight), a value with plausibility 0.2 still
  reached ~0.77 confidence due to near-perfect structural signals. At 0.35, the
  same value reaches ~0.62, placing it firmly in the human-review band.

── Two-tier confidence model ─────────────────────────────────────────────────

Confidence threshold: auto_accept_threshold (default 0.75, set per template).

  >= 0.75  Auto-accept — field value is written directly to ClaimCenter.
  <  0.75  Human review — field is flagged in review_flags; adjuster confirms.

There is NO separate reject tier. Very-low-quality extractions (plausibility
<= 0.3, e.g., heavily OCR-garbled location strings) score in the 0.55–0.75
review band, NOT below 0.55, because structural signals (label proximity, multi-
pattern agreement) remain satisfied even for garbage values that match a template
pattern. This is by design: the system surfaces a best-effort extraction with a
review flag rather than discarding the candidate silently. The adjuster can then
confirm, correct, or clear the value.

Populating the < 0.55 band would require either a plausibility weight >= 0.45
(which would depress scores for fields without registered plausibility functions)
or active candidate rejection when plausibility is critically low (a future option
if per-field policy is warranted).

See core/plausibility.py for registered semantic sanity functions.

── Priority tiebreaker ────────────────────────────────────────────────────────

Priority is a tiebreaker bonus capped at +0.02 (reduced from +0.05).
Formula: min(0.02, max(0.0, (100 - strategy_priority) * 0.0002))
Lower priority number = higher bonus (priority 1 = max bonus).

Rejected candidates score to 0.0 immediately.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from core.candidate import Candidate, ScoreBreakdown
from core.plausibility import plausibility_score
from extractors._geometry import aabb_overlap

if TYPE_CHECKING:
    from core.template_schema import FieldDefinition


WEIGHTS: dict[str, float] = {
    "label_proximity":       0.15,
    "validator_pass":        0.15,
    "regex_confidence":      0.05,
    "ocr_confidence":        0.10,
    "page_preference":       0.05,
    "region_alignment":      0.15,
    "multiline_consistency": 0.35,
    "overlap_penalty":      -0.05,
}


# ── Pattern specificity helpers ───────────────────────────────────────────────

def _raw_specificity(pattern: str) -> float:
    """Heuristic raw specificity score for a single regex pattern string."""
    s = 0.50
    s += len(re.findall(r'\\d', pattern)) * 0.08   # \d — digit class
    s += len(re.findall(r'\\w', pattern)) * 0.03   # \w — word char (less specific)
    s += len(re.findall(r'\[[^\]]+\]', pattern)) * 0.05  # [...] char classes
    s += len(re.findall(r'(?<!\[)(?<!\\)\^', pattern)) * 0.06  # ^ line-start anchor
    s += len(re.findall(r'(?<!\\)\$', pattern)) * 0.06          # $ line-end anchor
    s += len(re.findall(r'\\b', pattern)) * 0.04               # \b word boundary
    literals = re.findall(r'(?<![\\(|{])[A-Za-z]{3,}', pattern)
    s += min(len(literals), 8) * 0.025  # fixed literal words boost specificity
    s -= len(re.findall(r'\.\+(?!\?)', pattern)) * 0.20  # .+ greedy — penalise
    s -= len(re.findall(r'\.\*(?!\?)', pattern)) * 0.25  # .* greedy — penalise more
    return max(0.05, s)


# ── Individual signals ────────────────────────────────────────────────────────

def _label_proximity(
    c: Candidate,
    label_terms: list[str] = (),
    doc_text: str = "",
) -> float:
    """
    Docling path: bbox-based spatial distance (unchanged).
    pdfplumber path: character distance from regex match start to nearest
      occurrence of any declared label_text term in the document.
    """
    # ── Docling path (unchanged) ─────────────────────────────────────
    if c.bbox is not None and c.label_bbox is not None:
        dist = c.metadata.get("label_distance")
        if dist is None:
            return 0.5
        if dist <= 30:
            return 1.0
        if dist >= 200:
            return 0.0
        return 1.0 - ((dist - 30) / 170.0)

    # ── pdfplumber path ──────────────────────────────────────────────
    if not label_terms:
        return 0.5   # no label hints declared → neutral

    if not c.match_span or not doc_text:
        return 0.1   # label hints exist but can't locate in text

    match_start = c.match_span[0]
    # Search in a window centred just before the match (labels precede values)
    win_start = max(0, match_start - 80)
    win_end   = min(len(doc_text), match_start + 60)
    window    = doc_text[win_start:win_end]

    best_dist: float = float("inf")
    for term in label_terms:
        try:
            for m in re.finditer(re.escape(term), window, re.IGNORECASE):
                # Absolute position of this label occurrence in doc
                label_abs_start = win_start + m.start()
                dist = match_start - label_abs_start
                if dist >= -20:   # slight negative allowed (label inside pattern)
                    best_dist = min(best_dist, max(0.0, float(dist)))
        except re.error:
            continue

    if best_dist == float("inf"):
        return 0.1   # no label found in window
    if best_dist <= 30:
        return 1.0
    if best_dist <= 80:
        return 0.7
    if best_dist <= 200:
        return 0.4
    return 0.1


def _validator_pass(c: Candidate, num_validators: int) -> float:
    if num_validators == 0:
        return 1.0      # no validators declared → neutral pass
    if c.rejected:
        return 0.0
    passed = sum(1 for v in c.validation_results if v.passed)
    return passed / num_validators


def _regex_confidence(c: Candidate) -> float:
    """1.0 if the value was constrained by a regex pattern; 0.5 otherwise."""
    return 1.0 if c.match_pattern else 0.5


def _ocr_confidence(
    c: Candidate,
    field_candidates: list[Candidate] = (),
) -> float:
    """
    Docling path: real per-word OCR confidence from the layout engine.
    pdfplumber path: pattern specificity score, normalised within the field's
      candidate pool so the most specific pattern scores ~1.0 and the most
      permissive scores ~0.4.
    """
    # ── Docling path (unchanged) ─────────────────────────────────────
    if c.ocr_confidence is not None:
        return c.ocr_confidence

    # ── pdfplumber path: pattern specificity ─────────────────────────
    if not c.match_pattern:
        return 0.70   # no pattern metadata — neutral

    this_raw = _raw_specificity(c.match_pattern)

    peer_patterns = {
        fc.match_pattern
        for fc in field_candidates
        if fc.source_strategy == "global_regex" and fc.match_pattern
    }

    if len(peer_patterns) <= 1:
        # Single pattern seen — map raw score to [0.40, 1.00]
        return round(max(0.40, min(1.00, 0.40 + (this_raw / 2.5) * 0.60)), 4)

    all_raws = [_raw_specificity(p) for p in peer_patterns]
    mn, mx = min(all_raws), max(all_raws)
    if mx == mn:
        return 0.70   # all patterns equally specific
    normalised = 0.40 + (this_raw - mn) / (mx - mn) * 0.60
    return round(max(0.40, min(1.00, normalised)), 4)


def _page_preference(
    c: Candidate,
    doc_text_len: int = 0,
    expected_position: str | None = None,
) -> float:
    """
    Docling path: page-1 bias (unchanged).
    pdfplumber path: relative document position (match_span / doc length)
      evaluated against the field's declared expected_position.
    """
    # ── Docling path (unchanged) ─────────────────────────────────────
    if c.page is not None:
        return 1.0 if c.page == 1 else 0.7

    # ── pdfplumber path: document position ──────────────────────────
    if not c.match_span or doc_text_len == 0:
        return 0.5

    rel = c.match_span[0] / doc_text_len  # 0.0 = start, 1.0 = end

    if expected_position == "header":
        if rel <= 0.25:
            return 1.0
        if rel <= 0.50:
            return 0.70
        return 0.40

    if expected_position == "footer":
        if rel >= 0.75:
            return 1.0
        if rel >= 0.50:
            return 0.70
        return 0.40

    return 0.5   # "any" or None → neutral


def _region_alignment(
    c: Candidate,
    field_candidates: list[Candidate] = (),
) -> float:
    """
    Docling path: anchor_region spatial check (placeholder, unchanged).
    pdfplumber path: multi-pattern agreement — how many non-rejected
      candidates for this field agree on the same (normalised) value.

    Scoring:
      3+ candidates agree on this value → 1.00
      2 candidates agree              → 0.85
      Only 1 candidate has this value but pool has conflicts → 0.30
      Only 1 candidate (no conflicts)  → 0.60
    """
    # ── Docling path: keep placeholder ──────────────────────────────
    if c.bbox is not None and c.label_bbox is not None:
        return 0.5

    # ── pdfplumber path: multi-pattern agreement ─────────────────────
    non_rejected = [fc for fc in field_candidates if not fc.rejected]
    if len(non_rejected) <= 1:
        return 0.60   # single match — no corroboration

    def _norm(v: str) -> str:
        return v.strip().lower()

    this_norm   = _norm(c.value)
    agreements  = sum(1 for fc in non_rejected if _norm(fc.value) == this_norm)
    unique_vals = {_norm(fc.value) for fc in non_rejected}

    if agreements >= 3:
        return 1.00
    if agreements == 2:
        return 0.85
    # agreements == 1: only this candidate holds this value
    if len(unique_vals) > 1:
        return 0.30   # conflicting candidates exist — low confidence
    return 0.60       # only one unique value across all candidates, just one match


def _multiline_consistency(c: Candidate) -> float:
    """
    Docling path: multi-line value coherence (placeholder, unchanged → 0.5).
    pdfplumber path: value plausibility via the PLAUSIBILITY_REGISTRY.
    """
    # Docling candidates have a bbox; pdfplumber ones do not
    if c.bbox is not None:
        return 0.5   # Docling placeholder — unchanged

    return plausibility_score(c.field_id, c.value)


def _overlap_penalty(c: Candidate) -> float:
    """Penalty when value bbox overlaps the label bbox (Docling only)."""
    if c.bbox is None or c.label_bbox is None:
        return 0.0
    return 1.0 if aabb_overlap(c.bbox, c.label_bbox) else 0.0


# ── Combine ───────────────────────────────────────────────────────────────────

def score_candidate(
    c: Candidate,
    num_validators: int,
    *,
    label_terms: list[str] = (),
    expected_position: str | None = None,
    doc_text: str = "",
    field_candidates: list[Candidate] = (),
) -> None:
    """Mutates c.score (breakdown) and c.confidence (final).

    Extra keyword arguments carry context needed by the pdfplumber scoring path:
      label_terms       — fdef.label_text from the FieldDefinition
      expected_position — fdef.expected_position ("header" | "footer" | "any" | None)
      doc_text          — full document markdown text
      field_candidates  — all Candidate objects for this field (for agreement scoring)
    """
    if c.rejected:
        c.confidence = 0.0
        c.score.final = 0.0
        return

    doc_text_len = len(doc_text)

    sig = ScoreBreakdown(
        label_proximity       = _label_proximity(c, label_terms, doc_text),
        validator_pass        = _validator_pass(c, num_validators),
        regex_confidence      = _regex_confidence(c),
        ocr_confidence        = _ocr_confidence(c, field_candidates),
        page_preference       = _page_preference(c, doc_text_len, expected_position),
        region_alignment      = _region_alignment(c, field_candidates),
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

    # Priority tiebreaker — capped at +0.02 (reduced from +0.05)
    pri = max(0, c.strategy_priority)
    priority_bonus = min(0.02, max(0.0, (100 - pri) * 0.0002))
    score += priority_bonus

    sig.final = max(0.0, min(1.0, score))
    c.score     = sig
    c.confidence = sig.final
