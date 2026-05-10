"""Bbox geometry helpers — coords are [l, t, r, b] in PDF points,
BOTTOMLEFT origin (Docling default). t > b, larger y is higher on page.

These helpers are the only place direction logic should live, so all
spatially-aware strategies behave consistently.
"""
from __future__ import annotations


BBox = list[float]


def bbox_center(b: BBox) -> tuple[float, float]:
    return (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0


def bbox_width(b: BBox) -> float:
    return b[2] - b[0]


def bbox_height(b: BBox) -> float:
    return abs(b[1] - b[3])


def vertical_overlap(a: BBox, b: BBox, slack: float = 0.0) -> bool:
    a_lo = min(a[1], a[3]) - slack
    a_hi = max(a[1], a[3]) + slack
    b_lo = min(b[1], b[3]) - slack
    b_hi = max(b[1], b[3]) + slack
    return max(a_lo, b_lo) < min(a_hi, b_hi)


def horizontal_overlap(a: BBox, b: BBox, slack: float = 0.0) -> bool:
    a_lo, a_hi = a[0] - slack, a[2] + slack
    b_lo, b_hi = b[0] - slack, b[2] + slack
    return max(a_lo, b_lo) < min(a_hi, b_hi)


def distance(a: BBox, b: BBox) -> float:
    """Euclidean distance between bbox centers (in points)."""
    ax, ay = bbox_center(a)
    bx, by = bbox_center(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def is_in_direction(label: BBox, cand: BBox, direction: str) -> bool:
    """Is `cand` positioned in `direction` relative to `label` on the page?

    Slack — half the label dimension on the perpendicular axis — accepts
    candidates slightly off-row/off-column for typical form-field offsets,
    but not so generous as to jump into the next row.
    """
    label_cx, label_cy = bbox_center(label)
    cand_cx,  cand_cy  = bbox_center(cand)
    h_slack = max(bbox_height(label) * 0.5, 2.0)
    w_slack = max(bbox_width(label)  * 0.5, 2.0)

    if direction == "right":
        return cand_cx > label_cx and vertical_overlap(label, cand, h_slack)
    if direction == "left":
        return cand_cx < label_cx and vertical_overlap(label, cand, h_slack)
    if direction == "below":
        return cand_cy < label_cy and horizontal_overlap(label, cand, w_slack)
    if direction == "above":
        return cand_cy > label_cy and horizontal_overlap(label, cand, w_slack)
    if direction == "self":
        # Sentinel: caller handles "extract value from inside the label" via value_pattern.
        return False
    raise ValueError(f"unknown direction: {direction!r}")


def aabb_overlap(a: BBox, b: BBox) -> bool:
    """Do two bboxes overlap at all (axis-aligned)?"""
    if a[2] < b[0] or b[2] < a[0]:
        return False
    a_top = max(a[1], a[3]); a_bot = min(a[1], a[3])
    b_top = max(b[1], b[3]); b_bot = min(b[1], b[3])
    if a_top < b_bot or b_top < a_bot:
        return False
    return True
