"""global_regex — find a uniquely-shaped value anywhere in the markdown.

Used for fields with strong shape constraints — FEIN, SSN, NAICS code,
phone, email, URL, etc. Operates on `document.markdown` only; if the
template wants spatial signal too, pair this with a spatial_label
strategy at higher priority.

Patterns may use a `(?P<value>...)` named group OR plain capturing group;
if neither is present we use the full match. Multiple patterns are tried
in order — every match across every pattern becomes a Candidate (the
orchestrator then validates and ranks).
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from backend.core.candidate import Candidate
from backend.core.document_model import Document
from backend.extractors.base import register


class GlobalRegexConfig(BaseModel):
    patterns: list[str]
    flags:    list[Literal["IGNORECASE", "MULTILINE", "DOTALL"]] = Field(default_factory=list)


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


@register("global_regex")
class GlobalRegexStrategy:
    name = "global_regex"

    def run(self, document: Document, field_id: str, config: dict) -> list[Candidate]:
        cfg = GlobalRegexConfig.model_validate(config)
        text = document.markdown or ""
        if not text:
            return []
        flags = _flags(cfg.flags)

        out: list[Candidate] = []
        for pidx, pattern_str in enumerate(cfg.patterns):
            try:
                pat = re.compile(pattern_str, flags)
            except re.error:
                continue
            for m in pat.finditer(text):
                groupdict = m.groupdict() or {}
                if "value" in groupdict and groupdict["value"] is not None:
                    val = groupdict["value"]
                elif m.groups():
                    val = m.group(1)
                else:
                    val = m.group(0)
                if val is None:
                    continue
                val = val.strip()
                if not val:
                    continue
                out.append(Candidate(
                    field_id        = field_id,
                    value           = val,
                    source_strategy = self.name,
                    raw_match_text  = m.group(0),
                    match_pattern   = pattern_str,
                    match_span      = [m.start(), m.end()],
                    metadata        = {"pattern_index": pidx},
                ))
        return out
