"""Candidate model — Layer 4.

The universal extraction currency. Every extraction strategy emits zero
or more Candidates per field. Candidates flow through validation, then
scoring, then the highest-scoring valid candidate per field becomes the
final extracted value.

Carries everything needed for:
  - validation
  - scoring
  - selection
  - audit (bbox + page + matched label + raw match + score breakdown)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# A bbox as [l, t, r, b] in PDF points, BOTTOMLEFT origin (Docling default).
BBox = list[float]


@dataclass
class ScoreBreakdown:
    """Per-signal contributions to the final confidence score."""
    label_proximity:       float = 0.0
    validator_pass:        float = 0.0
    ocr_confidence:        float = 0.0
    page_preference:       float = 0.0
    region_alignment:      float = 0.0
    regex_confidence:      float = 0.0
    overlap_penalty:       float = 0.0
    multiline_consistency: float = 0.0
    final:                 float = 0.0


@dataclass
class ValidationResult:
    """Result of one validator applied to one candidate."""
    validator_type: str
    passed:         bool
    reason:         str | None = None


@dataclass
class Candidate:
    """One extracted value candidate from a single strategy run."""

    # ── Identity ─────────────────────────────────────────────────────
    field_id:        str
    value:           str
    source_strategy: str

    # ── Provenance (audit) ──────────────────────────────────────────
    page:            int | None  = None
    bbox:            BBox | None = None
    label_text:      str | None  = None
    label_bbox:      BBox | None = None
    raw_match_text:  str | None  = None
    match_pattern:   str | None  = None
    match_span:      list[int] | None = None
    ocr_confidence:  float | None     = None

    # ── Scoring ──────────────────────────────────────────────────────
    confidence:        float          = 0.0
    score:             ScoreBreakdown = field(default_factory=ScoreBreakdown)
    strategy_priority: int            = 100

    # ── Validation ───────────────────────────────────────────────────
    validation_results: list[ValidationResult] = field(default_factory=list)
    rejected:           bool                   = False

    # ── Free-form trace for strategies/debug ─────────────────────────
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── Convenience ──────────────────────────────────────────────────
    @property
    def passed_validation(self) -> bool:
        return not self.rejected

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        v = self.value if len(self.value) <= 30 else self.value[:27] + "..."
        return (f"Candidate({self.field_id!r}={v!r} "
                f"via {self.source_strategy} conf={self.confidence:.2f}"
                f"{' REJECTED' if self.rejected else ''})")


# ── Helpers ──────────────────────────────────────────────────────────

def best(cands: list[Candidate]) -> Candidate | None:
    """Return the highest-confidence non-rejected Candidate, or None."""
    valid = [c for c in cands if not c.rejected]
    if not valid:
        return None
    return max(valid, key=lambda c: c.confidence)
