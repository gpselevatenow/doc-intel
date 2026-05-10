"""Validation engine â€” Layer 6.

Applies a list of `ValidatorRule` entries to each Candidate. A failed
validator marks the candidate `rejected` but subsequent validators
still run, so the audit trail captures the full failure list.

Built-in expected-type patterns cover phone / date / money / email /
url / fein / ssn / naics / sic / integer. Additional shape validators
(date_format, phone_format, fein_format) are aliases that delegate to
the same _TYPE_PATTERNS â€” they exist for template clarity.
"""
from __future__ import annotations

import re

from core.candidate import Candidate, ValidationResult
from core.template_schema import ValidatorRule


_TYPE_PATTERNS: dict[str, re.Pattern] = {
    "phone":   re.compile(r"^[\d\s().+\-x]{10,}$"),
    "date":    re.compile(r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$"),
    "money":   re.compile(r"^\$?\s*[\d,]+(?:\.\d{2})?$"),
    "email":   re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"),
    "url":     re.compile(r"^(?:https?://|www\.)[A-Za-z0-9.\-]+(?:/[^\s]*)?$",
                          re.IGNORECASE),
    "fein":    re.compile(r"^\d{2}-?\d{7}$"),
    "ssn":     re.compile(r"^\d{3}-\d{2}-\d{4}$"),
    "naics":   re.compile(r"^\d{4,6}$"),
    "sic":     re.compile(r"^\d{4}$"),
    "integer": re.compile(r"^-?\d+$"),
}


def _apply(rule: ValidatorRule, value: str) -> tuple[bool, str | None]:
    """Returns (passed, reason_if_failed). Reason is None on pass."""
    t = rule.type

    if t == "regex_match":
        pat = rule.pattern or ""
        if not pat:
            return False, "no pattern provided"
        ok = re.search(pat, value) is not None
        return ok, (None if ok else f"value did not match {pat!r}")

    if t == "reject_if_contains":
        for s in (rule.values or []):
            if s.upper() in value.upper():
                return False, f"contains forbidden phrase {s!r}"
        return True, None

    if t == "reject_if_starts_with":
        for s in (rule.values or []):
            if value.upper().startswith(s.upper()):
                return False, f"starts with forbidden phrase {s!r}"
        return True, None

    if t == "min_length":
        n = int(rule.value or 0)
        ok = len(value) >= n
        return ok, (None if ok else f"length {len(value)} < {n}")

    if t == "max_length":
        n = int(rule.value or 0)
        ok = len(value) <= n
        return ok, (None if ok else f"length {len(value)} > {n}")

    if t == "expected_type":
        ty = (rule.value or "").lower()
        pat = _TYPE_PATTERNS.get(ty)
        if pat is None:
            return False, f"unknown type {ty!r}"
        ok = pat.match(value) is not None
        return ok, (None if ok else f"not a valid {ty}")

    if t in ("date_format", "phone_format", "fein_format"):
        ty = t.replace("_format", "")
        pat = _TYPE_PATTERNS[ty]
        ok = pat.match(value) is not None
        return ok, (None if ok else f"not a valid {ty}")

    if t == "blacklist":
        if value in (rule.values or []):
            return False, "value is blacklisted"
        return True, None

    if t == "whitelist":
        wl = rule.values or []
        if value not in wl:
            return False, "value not in whitelist"
        return True, None

    return False, f"unknown validator type {t!r}"


def validate_candidate(c: Candidate, rules: list[ValidatorRule]) -> None:
    """Apply each rule in order. Mutates `c.validation_results` and `c.rejected`."""
    for rule in rules:
        passed, reason = _apply(rule, c.value)
        c.validation_results.append(ValidationResult(
            validator_type = rule.type,
            passed         = passed,
            reason         = reason,
        ))
        if not passed:
            c.rejected = True


def validate_all(
    cands_per_field: dict[str, list[Candidate]],
    rules_by_field:  dict[str, list[ValidatorRule]],
) -> None:
    """Apply per-field validators to every Candidate of every field."""
    for field_id, cands in cands_per_field.items():
        rules = rules_by_field.get(field_id, [])
        for c in cands:
            validate_candidate(c, rules)

