"""
lookups/ — versioned reference data for insurance document extraction.

Public API (import from here, not from sub-modules):
    naic_lookup(cocode)          → carrier name or None
    naic_search(name_fragment)   → list of (cocode, name) matches
    mmucc_field(element_id)      → MMUCC element descriptor dict or None
    mmucc_decode(element_id, code) → human-readable value or raw code
    decode_state(state, table, code) → decoded value or raw code
    citation_lookup(state, statute)  → description or None
    TABLE_VERSION                → dict mapping table name → version string
"""

from lookups.naic_carriers import lookup as naic_lookup, search as naic_search
from lookups.mmucc_schema import field as mmucc_field, decode as mmucc_decode
from lookups.state_codes import decode as decode_state
from lookups.state_statutes import lookup as citation_lookup
from lookups._meta import TABLE_VERSION

__all__ = [
    "naic_lookup",
    "naic_search",
    "mmucc_field",
    "mmucc_decode",
    "decode_state",
    "citation_lookup",
    "TABLE_VERSION",
]
