"""spatial_label â€” primary extraction strategy for forms.

Anchors on a label string near the value, then captures the value in
the configured direction (right / left / below / above / self) within
a search radius.

The "self" direction is special: the value is extracted from inside
the label item itself via `value_pattern` (capturing group). Used for
forms where the label and value share a single text item, e.g.
"DATE (MM/DD/YYYY)" with the date co-mingled into the same item.

Config validation is done by `SpatialLabelConfig` â€” the strategy-specific
pydantic model. Templates pass an opaque dict; we validate on entry.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from core.candidate import Candidate
from core.document_model import Block, Document
from extractors._geometry import distance, is_in_direction
from extractors.base import register


# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class SpatialLabelConfig(BaseModel):
    """Config slice for a spatial_label strategy entry in a template."""
    labels:        list[str]                                      # alternative label patterns
    label_match:   Literal["regex", "literal", "exact"] = "regex"
    label_flags:   list[Literal["IGNORECASE", "MULTILINE", "DOTALL"]] = Field(default_factory=list)
    label_match_index: int = 0
    direction:     Literal["right", "left", "below", "above", "self"] = "right"
    search_radius: float   = 80.0
    value_pattern: str | None = None
    value_flags:   list[Literal["IGNORECASE", "MULTILINE", "DOTALL"]] = Field(default_factory=list)
    value_filter:  Literal["nearest", "leftmost", "rightmost"] = "nearest"
    skip_value_labels: list[str] = Field(default_factory=list)


_FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE":  re.MULTILINE,
    "DOTALL":     re.DOTALL,
}


def _flags(names: list[str]) -> int:
    out = 0
    for n in names:
        out |= _FLAG_MAP.get(n, 0)
    return out


def _compile_label(pat: str, mode: str, flags: int) -> re.Pattern:
    if mode == "regex":
        return re.compile(pat, flags)
    if mode == "literal":
        return re.compile(re.escape(pat), flags | re.IGNORECASE)
    # exact
    return re.compile(rf"^{re.escape(pat)}$", flags)


# â”€â”€ Block searching â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _find_label_blocks(blocks: list[Block], pattern: re.Pattern) -> list[Block]:
    return [b for b in blocks if pattern.search(b.text)]


def _find_value_block(
    blocks:        list[Block],
    label_block:   Block,
    direction:     str,
    max_distance:  float,
    value_re:      re.Pattern | None,
    skip_labels:   tuple[str, ...],
    value_filter:  str,
) -> tuple[Block | None, float]:
    """Returns (best_value_block_or_None, distance_to_label)."""
    candidates: list[tuple[float, float, Block]] = []
    for b in blocks:
        if b is label_block:
            continue
        if b.page != label_block.page:
            continue
        if b.label and b.label in skip_labels:
            continue
        if not b.text.strip():
            continue
        if not is_in_direction(label_block.bbox, b.bbox, direction):
            continue
        d = distance(label_block.bbox, b.bbox)
        if max_distance and d > max_distance:
            continue
        if value_re and not value_re.search(b.text):
            continue
        candidates.append((d, b.bbox[0], b))
    if not candidates:
        return None, 0.0
    if value_filter == "leftmost":
        candidates.sort(key=lambda c: (c[1], c[0]))
    elif value_filter == "rightmost":
        candidates.sort(key=lambda c: (-c[1], c[0]))
    else:
        candidates.sort(key=lambda c: c[0])
    d, _, b = candidates[0]
    return b, d


# â”€â”€ Strategy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@register("spatial_label")
class SpatialLabelStrategy:
    name = "spatial_label"

    def run(self, document: Document, field_id: str, config: dict) -> list[Candidate]:
        cfg = SpatialLabelConfig.model_validate(config)
        flags = _flags(cfg.label_flags)
        blocks = document.all_blocks()
        skip_labels = tuple(cfg.skip_value_labels)
        value_re = (re.compile(cfg.value_pattern, _flags(cfg.value_flags))
                    if cfg.value_pattern else None)

        out: list[Candidate] = []

        # First label string that matches wins for this strategy entry â€”
        # consistent with legacy spatial_engine semantics. Multiple `labels`
        # entries are alternatives, not multiple shots.
        for label_str in cfg.labels:
            label_re = _compile_label(label_str, cfg.label_match, flags)
            matches = _find_label_blocks(blocks, label_re)
            if not matches:
                continue
            if cfg.label_match_index >= len(matches):
                continue
            label_block = matches[cfg.label_match_index]

            # direction == "self" â†’ value captured from label_block.text via value_pattern
            if cfg.direction == "self":
                if value_re is None:
                    continue
                m = value_re.search(label_block.text)
                if not m:
                    continue
                captured = m.group(1) if m.groups() else m.group(0)
                if captured is None:
                    continue
                out.append(Candidate(
                    field_id        = field_id,
                    value           = captured.strip(),
                    source_strategy = self.name,
                    page            = label_block.page,
                    bbox            = list(label_block.bbox),
                    label_text      = label_block.text,
                    label_bbox      = list(label_block.bbox),
                    raw_match_text  = label_block.text,
                    match_pattern   = cfg.value_pattern,
                    metadata        = {
                        "direction": "self",
                        "label_pattern": label_str,
                        "label_distance": 0.0,
                    },
                ))
                # Don't try further labels once we've matched
                return out

            value_block, d = _find_value_block(
                blocks, label_block,
                cfg.direction, cfg.search_radius, value_re,
                skip_labels, cfg.value_filter,
            )
            if value_block is None:
                continue
            out.append(Candidate(
                field_id        = field_id,
                value           = value_block.text,
                source_strategy = self.name,
                page            = value_block.page,
                bbox            = list(value_block.bbox),
                label_text      = label_block.text,
                label_bbox      = list(label_block.bbox),
                raw_match_text  = value_block.text,
                metadata        = {
                    "direction": cfg.direction,
                    "label_pattern": label_str,
                    "label_distance": d,
                },
            ))
            return out

        return out

