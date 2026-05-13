"""
Checkbox grid extractor strategy.

Identifies which option in a multi-choice checkbox group is selected
in the extracted document text.

Handles all common PDF/OCR checkbox rendering variants:
  [X] [x] [✓] [✗]  — bracket-style (most common in digital PDFs)
  ☑ ☒ ✅            — Unicode filled checkboxes
  ✓ ✔ ✗            — Standalone checkmarks
  ■ ● ▪             — Filled geometric shapes
  (X) (x)           — Parenthesis-style

Template config:
  options:        list[str] — option labels to scan for (in preference order)
  section_anchor: str       — optional text anchor to narrow search window
                              (first 600 chars after anchor are scanned)

Example (TX CR-3 weather field):
  {
    "strategy": "checkbox_grid",
    "config": {
      "options": ["Clear", "Cloudy", "Rain", "Sleet/Hail", "Snow",
                  "Fog/Smog/Smoke", "Blowing Sand/Soil/Dirt/Snow",
                  "Severe Crosswinds", "Other"],
      "section_anchor": "WEATHER"
    }
  }
"""
from __future__ import annotations
import re
from pydantic import BaseModel

from core.candidate import Candidate
from core.document_model import Document
from extractors.base import Strategy, register


class CheckboxGridConfig(BaseModel):
    options: list[str]
    section_anchor: str = ""


# All characters/sequences that indicate a checked checkbox
_CHECKED_RE = re.compile(
    r'(?:'
    r'\[[Xx✓✗●■✔]\]'         # [X] [x] [✓] etc.
    r'|[☑☒✅]'                 # Unicode filled checkboxes
    r'|[✓✔](?!\w)'             # Standalone checkmarks (not mid-word)
    r'|■(?!\w)'                 # Filled square
    r'|●(?!\w)'                 # Filled circle / radio button
    r'|▪(?!\w)'                 # Small filled square
    r'|\([Xx]\)'                # (X) or (x)
    r')',
    re.UNICODE
)

# All characters/sequences that indicate an UNCHECKED checkbox
# (used to verify we're not matching a stray mark in the unchecked pattern)
_UNCHECKED_RE = re.compile(
    r'(?:\[\s*\]|[☐□○])',
    re.UNICODE
)


@register("checkbox_grid")
class CheckboxGridStrategy(Strategy):
    """Extract the checked option from a checkbox / radio-button group."""

    def run(self, document: Document, field_id: str, config: dict) -> list[Candidate]:
        cfg = CheckboxGridConfig.model_validate(config)
        text = document.markdown or ""
        if not text or not cfg.options:
            return []

        # Narrow search to a window after the section anchor if provided
        search_text = text
        if cfg.section_anchor:
            m = re.search(re.escape(cfg.section_anchor), text, re.IGNORECASE)
            if m:
                search_text = text[m.start(): m.start() + 800]

        candidates: list[Candidate] = []

        for option in cfg.options:
            escaped = re.escape(option)

            # Pattern 1: checked marker immediately before option label (≤3 chars gap)
            pat_before = re.compile(
                rf'(?:{_CHECKED_RE.pattern})\s{{0,3}}{escaped}',
                re.IGNORECASE | re.UNICODE
            )
            # Pattern 2: option label immediately followed by checked marker (≤3 chars gap)
            pat_after = re.compile(
                rf'{escaped}\s{{0,3}}(?:{_CHECKED_RE.pattern})',
                re.IGNORECASE | re.UNICODE
            )
            # Pattern 3: option label followed by "Yes" or "Selected" (some FL/PA forms)
            pat_yes = re.compile(
                rf'{escaped}\s*[:\-]?\s*(?:Yes|Selected|Checked)\b',
                re.IGNORECASE
            )
            # Pattern 4: "X" or "x" as a standalone word before option (worst-case OCR)
            pat_x_word = re.compile(
                rf'\bX\b\s{{1,4}}{escaped}',
                re.IGNORECASE
            )

            for pat, source in (
                (pat_before, "checkbox_before"),
                (pat_after,  "checkbox_after"),
                (pat_yes,    "checkbox_yes_marker"),
                (pat_x_word, "checkbox_x_word"),
            ):
                m = pat.search(search_text)
                if m:
                    candidates.append(Candidate(
                        field_id=field_id,
                        value=option,
                        confidence=0.85 if "before" in source or "after" in source else 0.70,
                        source_strategy="checkbox_grid",
                        page=1,
                        raw_match_text=m.group(0)[:80],
                        metadata={"pattern": source, "option": option}
                    ))
                    break  # Found this option — move to next option

        if not candidates:
            return []

        # Deduplicate (same option matched by multiple patterns → keep highest conf)
        seen: dict[str, Candidate] = {}
        for c in candidates:
            if c.value not in seen or c.confidence > seen[c.value].confidence:
                seen[c.value] = c

        return list(seen.values())
