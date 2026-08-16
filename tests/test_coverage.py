"""EFL701 - single-pass swath requirement."""

from __future__ import annotations

import pytest

from eo_feasibility_lint.models import FAIL, PASS


@pytest.mark.parametrize(
    ("mission_id", "swath_km"),
    [("sentinel-2", 290), ("sentinel-1-iw", 250), ("landsat-8", 185)],
)
def test_exact_swath_meets_requirement(result, codes, mission_id, swath_km):
    outcome = result(mission_id, coverage={"min_single_pass_swath_km": swath_km})
    assert outcome.verdict == PASS
    assert codes(outcome) == []


def test_swath_narrower_than_required_fails(result, codes):
    outcome = result("sentinel-1-iw", coverage={"min_single_pass_swath_km": 300})
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL701"]
    assert outcome.findings[0].capability == {"swath_km": 250}


def test_sentinel2_is_the_widest_supported_swath(result):
    assert result("sentinel-2", coverage={"min_single_pass_swath_km": 290}).verdict == PASS
    assert result("sentinel-2", coverage={"min_single_pass_swath_km": 300}).verdict == FAIL


def test_mosaicking_is_not_considered(result):
    """Two Landsat passes are not combined to reach 300 km."""
    outcome = result("landsat-8-9", coverage={"min_single_pass_swath_km": 300})
    assert outcome.verdict == FAIL
    assert "multiple passes is not evaluated" in outcome.findings[0].message


def test_coverage_findings_cite_sources(result):
    outcome = result("landsat-8", coverage={"min_single_pass_swath_km": 300})
    assert outcome.findings[0].source_ids
