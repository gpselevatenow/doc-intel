"""Field-centric template schema — Layer 2.

Templates declare WHAT fields the user wants extracted. The platform
internally decides HOW (which strategies, with what config). Users
never name strategies in the normal flow — they highlight a value in
the UI and the auto-strategy-inference engine (Layer 9) writes the
strategy block into the template.

Each FieldDefinition carries its OWN strategy stack, validators, and
metadata. This is the OPPOSITE of the legacy extractor-centric shape
where extractors sat at the top level.

Stored in MongoDB collection `docling_templates`, versioned by
(template_id, version). The Beanie wrapper lives in
`app/models/template.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Field types ──────────────────────────────────────────────────────

class FieldType(str, Enum):
    """Semantic type — drives default validators, type-coercion, and renderers."""
    TEXT          = "text"
    NUMBER        = "number"
    INTEGER       = "integer"
    MONEY         = "money"
    DATE          = "date"
    TIME          = "time"
    EMAIL         = "email"
    PHONE         = "phone"
    URL           = "url"
    FEIN          = "fein"
    SSN           = "ssn"
    NAICS         = "naics"
    SIC           = "sic"
    PERSON_NAME   = "person_name"
    ORG_NAME      = "organization_name"
    ADDRESS       = "address"
    BOOL          = "bool"
    ENUM          = "enum"
    CHECKBOX      = "checkbox"
    LIST_OF_OBJECTS = "list_of_objects"


# ── Strategy entry ───────────────────────────────────────────────────
#
# `config` is intentionally `dict[str, Any]` so the template stores raw
# strategy configs. Each strategy validates its own config when invoked
# (extractors/{strategy_name}.py defines a pydantic config model).

StrategyName = Literal[
    "spatial_label",
    "global_regex",
    "nearby_text",
    "table_cell",
    "anchor_region",
    "advanced_table",
]


class FieldStrategy(BaseModel):
    """One strategy for extracting a field. Multiple stack; lower priority = tried first."""
    strategy: StrategyName
    priority: int = 1
    config:   dict[str, Any] = Field(default_factory=dict)


# ── Validator rule ───────────────────────────────────────────────────

ValidatorType = Literal[
    "regex_match",
    "reject_if_contains",
    "reject_if_starts_with",
    "min_length",
    "max_length",
    "expected_type",
    "blacklist",
    "whitelist",
    "date_format",
    "phone_format",
    "fein_format",
]


class ValidatorRule(BaseModel):
    """A single validation rule applied to candidates of a field."""
    type:    ValidatorType
    pattern: str | None = None
    values:  list[str] | None = None
    value:   Any | None = None


# ── Field definition ─────────────────────────────────────────────────

class FieldDefinition(BaseModel):
    """One field the user wants extracted."""
    field_id:     str
    display_name: str | None = None
    field_type:   FieldType
    required:     bool = False
    description:  str | None = None
    strategies:   list[FieldStrategy] = Field(default_factory=list)
    validators:   list[ValidatorRule] = Field(default_factory=list)


# ── Template (top-level) ─────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TemplateSchema(BaseModel):
    """A field-centric extraction template."""
    template_id:   str
    version:       str = "1.0"
    document_type: str
    domain:        str | None = None
    label:         str | None = None
    description:   str | None = None
    fields:        list[FieldDefinition] = Field(default_factory=list)
    auto_accept_threshold: float = 0.85
    created_at:    datetime = Field(default_factory=_utcnow)
    updated_at:    datetime = Field(default_factory=_utcnow)

    model_config = ConfigDict(extra="forbid")
