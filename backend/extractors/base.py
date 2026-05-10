"""Strategy protocol + registration decorator.

A Strategy is anything that can produce Candidates from a (Document,
field_id, config) triple. The registry maps strategy-name → class so
the orchestrator can dispatch by name from a template.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.candidate import Candidate
from backend.core.document_model import Document


@runtime_checkable
class Strategy(Protocol):
    """A strategy produces Candidates for one field from a Document."""
    name: str

    def run(self, document: Document, field_id: str, config: dict) -> list[Candidate]:
        ...


STRATEGY_REGISTRY: dict[str, type[Strategy]] = {}


def register(name: str):
    """Decorator: register a Strategy class under the given strategy name."""
    def _wrap(cls):
        cls.name = name
        STRATEGY_REGISTRY[name] = cls
        return cls
    return _wrap
