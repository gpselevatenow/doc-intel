# Schema Mismatch Decision — vehicles / parties / witnesses

**Status: AWAITING DECISION — do not fix until owner chooses path**

**Filed:** 2026-05-13
**Discovered in:** ground truth benchmark run, sample_full_report.pdf (tx_cr3)

---

## The Problem

The benchmark compares extracted field values against hand-labeled ground truth strings.
For `vehicles`, `parties`, and `witnesses`, the extractor produces rich nested JSON objects,
but the ground truth was labeled as flat comma-separated strings. The comparison fails
for every document on these three fields, inflating INCORRECT counts and suppressing F1.

This is a **labeling format mismatch**, not an extraction bug. The extractor is working as
designed — it extracts structured vehicle/party records. The question is: what should the
benchmark compare?

---

## Example (sample_full_report.pdf, field: vehicles)

**Ground truth (flat string):**
```
"LMK-4421 (TX), MRY-8820 (TX), CMV-3319 (TX)"
```

**Extractor output (rich JSON, first vehicle only):**
```json
{
  "vin": "2T3RWRFV9NC123456",
  "plate": "LMK-4421",
  "make": "Toyota",
  "year": "2022",
  "model": "RAV4 XLE AWD",
  "color": "Magnetic Gray Metallic",
  "damages": "Unknown",
  "owner_name": "Karen L. Whitfield",
  "owner_address": "4812 Ridgemont Drive, Fort Worth, TX 76131",
  "insurance_company": "State Farm Mutual Automobile Insurance Company",
  "policy_number": "SF-TX-4421-KLW-2026",
  "towed": "47 hrs by registered owner's spouse",
  "towing_company": "Unknown"
}
```

The benchmark's list normalizer splits on commas and compares as frozensets of strings.
A JSON string and a plate-only string cannot reconcile under that logic.

---

## The Two Paths

### Path A — Re-label ground truth to match extractor output

Label `vehicles`, `parties`, `witnesses` as JSON arrays matching the extractor's schema.
The benchmark comparison becomes a structured diff (e.g., check that each expected plate
appears in the extracted records).

**Pros:** Ground truth accurately reflects what we actually want to measure.
**Cons:** Re-labeling is expensive; the schema may evolve; benchmark comparator needs
a custom JSON diff mode for these three fields.

### Path B — Flatten extractor output on comparison

Add a benchmark-only normalization step that, for list fields, extracts the key identifier
(plate for vehicles, name for parties/witnesses) from each JSON object before comparing
against the flat ground truth string.

**Pros:** No re-labeling needed; ground truth stays human-readable.
**Cons:** Measures only plate/name recall — not whether the richer fields (VIN, insurance,
owner address) are correct. Hides structured extraction quality behind a thin proxy.

---

## Recommendation (not implemented)

Path B is faster to ship and unblocks the benchmark. Path A is the right long-term answer
once the vehicle/party schema stabilizes. A hybrid is possible: implement Path B now, add
a separate structured-field accuracy metric for vehicles/parties later.

**This file is a placeholder. No code changes until the owner makes a decision.**
