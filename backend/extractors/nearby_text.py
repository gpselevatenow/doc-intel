"""nearby_text â€” local search around a regex anchor in markdown.

Used as a fallback when spatial_label can't apply (scanned docs with
unreliable bbox, or narrative paragraphs where the labelâ€“value pairing
is loose). Operates on `document.markdown`.

Algorithm:
  1. Find every match of `anchor_pattern` in markdown.
  2. From each anchor's end position, take a window of `search_radius_chars`
     (or skip past the next newline first if `direction == "below"`).
  3. If `value_pattern` is given, capture from inside the window.
     Otherwise take the trimmed first line of the window.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from core.candidate import Candidate
from core.document_model import Document
from extractors.base import register


class NearbyTextConfig(BaseModel):
    anchor_pattern:      str
    direction:           Literal["right", "below"] = "right"
    search_radius_chars: int   = 200
    value_pattern:       str | None = None
    flags: list[Literal["IGNORECASE", "MULTILINE", "DOTALL"]] = Field(default_factory=list)


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


@register("nearby_text")
class NearbyTextStrategy:
    name = "nearby_text"

    def run(self, document: Document, field_id: str, config: dict) -> list[Candidate]:
        cfg = NearbyTextConfig.model_validate(config)
        text = document.markdown or ""
        if not text:
            return []
        flags    = _flags(cfg.flags)
        anchor_re = re.compile(cfg.anchor_pattern, flags)
        value_re  = re.compile(cfg.value_pattern, flags) if cfg.value_pattern else None

        out: list[Candidate] = []
        for m in anchor_re.finditer(text):
            slice_start = m.end()
            if cfg.direction == "below":
                nl = text.find("\n", slice_start)
                slice_start = (nl + 1) if nl != -1 else slice_start
            slice_end = min(len(text), slice_start + cfg.search_radius_chars)
            window = text[slice_start:slice_end]

            if value_re:
                vm = value_re.search(window)
                if not vm:
                    continue
                gd = vm.groupdict() or {}
                if "value" in gd and gd["value"] is not None:
                    val = gd["value"]
                elif vm.groups():
                    val = vm.group(1)
                else:
                    val = vm.group(0)
            else:
                val = window.strip().split("\n", 1)[0].strip()

            if not val:
                continue
            out.append(Candidate(
                field_id        = field_id,
                value           = val.strip(),
                source_strategy = self.name,
                raw_match_text  = window[:120],
                match_pattern   = cfg.anchor_pattern,
                match_span      = [m.start(), slice_end],
                metadata        = {
                    "direction":         cfg.direction,
                    "anchor_match_text": m.group(0),
                },
            ))
        return out

