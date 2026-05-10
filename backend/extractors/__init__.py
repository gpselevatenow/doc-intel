"""Extraction strategies — Layer 3.

Each strategy is a small module that:
  - accepts a canonical Document and a strategy config
  - returns zero or more Candidate objects with bbox/page/strategy/etc.

Strategies do NOT know what the field semantically *means* — they only
produce candidates that match the config. Validation, scoring, and
selection happen in the orchestrator (Layer 7).

Strategies register themselves at import time via @register("name").
The orchestrator looks up by strategy name from the template.
"""
from backend.extractors.base import STRATEGY_REGISTRY, Strategy, register

# Trigger strategy registration via import side-effect.
# Each module's @register("name") populates STRATEGY_REGISTRY at import time.
from backend.extractors import global_regex   # noqa: F401, E402
from backend.extractors import nearby_text    # noqa: F401, E402
from backend.extractors import spatial_label  # noqa: F401, E402

__all__ = ["Strategy", "STRATEGY_REGISTRY", "register"]
