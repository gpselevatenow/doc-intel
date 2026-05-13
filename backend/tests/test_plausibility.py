"""Unit tests for plausibility functions added in Tier 1.3.5."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.plausibility import plausibility_score


# ── location ──────────────────────────────────────────────────────────

class TestLocation:
    def test_good_highway(self):
        v = "I-35W Northbound between Exit 54A"
        assert plausibility_score("location", v) >= 0.9

    def test_good_mile_marker(self):
        v = "I-10 Westbound, Mile Marker 766.2"
        assert plausibility_score("location", v) >= 0.9

    def test_ocr_garbage(self):
        v = "(Route/RI-o45ad E) (Interstate) At Intersection With / MMileil eM aMrakerkrer 46.0 Latitude / Longit"
        assert plausibility_score("location", v) <= 0.3

    def test_too_short(self):
        assert plausibility_score("location", "Main") <= 0.3

    def test_starts_with_punctuation(self):
        assert plausibility_score("location", "(NON-HIGHWAY)") <= 0.3

    def test_neutral_no_road_term(self):
        v = "Near the downtown area somewhere"
        score = plausibility_score("location", v)
        assert 0.4 <= score <= 0.7


# ── accident_type ─────────────────────────────────────────────────────

class TestAccidentType:
    def test_good_chain_reaction(self):
        v = "Same Direction (Chain Reaction)"
        assert plausibility_score("accident_type", v) >= 0.9

    def test_good_rear_end(self):
        v = "3-vehicle rear-end collision"
        assert plausibility_score("accident_type", v) >= 0.9

    def test_too_short(self):
        assert plausibility_score("accident_type", "hit") <= 0.3

    def test_too_long(self):
        v = "x" * 160
        assert plausibility_score("accident_type", v) <= 0.3

    def test_truncated_but_vocab(self):
        v = "5-vehicle chain rear-end (fog-related"
        assert plausibility_score("accident_type", v) >= 0.9

    def test_neutral_no_vocab(self):
        v = "Something happened on the road"
        score = plausibility_score("accident_type", v)
        assert 0.4 <= score <= 0.7


# ── contributing_factors ───────────────────────────────────────────────

class TestContributingFactors:
    def test_good_coded_format(self):
        v = "[06] Driving Too Fast for Conditions | [14] Fatigued/Asleep L"
        assert plausibility_score("contributing_factors", v) >= 0.9

    def test_fragment_trailing_comma(self):
        v = "fog,"
        assert plausibility_score("contributing_factors", v) <= 0.3

    def test_too_short(self):
        assert plausibility_score("contributing_factors", "bad") <= 0.3

    def test_factor_vocab(self):
        v = "Speeding and driver distraction"
        assert plausibility_score("contributing_factors", v) >= 0.9

    def test_unknown_content(self):
        v = "Unknown factor"
        assert plausibility_score("contributing_factors", v) >= 0.9

    def test_no_vocab(self):
        v = "Something occurred on the road"
        score = plausibility_score("contributing_factors", v)
        assert 0.4 <= score <= 0.6


# ── property_damage ───────────────────────────────────────────────────

class TestPropertyDamage:
    def test_good_narrative(self):
        v = "Rear bumper assembly crushed and deformed; left tail lamp assembly shattered; rear lift"
        assert plausibility_score("property_damage", v) >= 0.9

    def test_parenthesized_label(self):
        v = "(NON-VEHICLE)"
        assert plausibility_score("property_damage", v) <= 0.3

    def test_barrier_damage(self):
        v = "I-10 WB centerline barrier — minor scraping along left side panel"
        assert plausibility_score("property_damage", v) >= 0.9

    def test_too_short(self):
        assert plausibility_score("property_damage", "dented") <= 0.3

    def test_no_damage_vocab(self):
        v = "Something was broken in the vicinity"
        score = plausibility_score("property_damage", v)
        assert 0.3 <= score <= 0.7

    def test_none_field(self):
        # None passed in as "—" handled upstream; test empty string
        assert plausibility_score("property_damage", "") <= 0.3


# ── ems_agency ────────────────────────────────────────────────────────

class TestEmsAgency:
    def test_good_garbled(self):
        v = "San Diego Regional Medical CenteErMS"
        assert plausibility_score("ems_agency", v) >= 0.9

    def test_na_value(self):
        assert plausibility_score("ems_agency", "N/A") <= 0.35

    def test_none_text(self):
        assert plausibility_score("ems_agency", "None") <= 0.35

    def test_phone_number(self):
        assert plausibility_score("ems_agency", "555-867-5309") <= 0.3

    def test_good_fire_dept(self):
        v = "Houston Fire Department EMS Unit 42"
        assert plausibility_score("ems_agency", v) >= 0.9

    def test_too_short(self):
        assert plausibility_score("ems_agency", "EMS") <= 0.3


# ── unregistered field still returns 0.5 ─────────────────────────────

def test_unregistered_field_neutral():
    assert plausibility_score("nonexistent_field", "anything") == 0.5
