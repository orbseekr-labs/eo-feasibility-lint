"""EFL401 / EFL402 - nominal revisit requirements."""

from __future__ import annotations

import pytest

from eo_feasibility_lint.models import FAIL, PASS


def test_revisit_too_slow_fails(result, codes):
    outcome = result("sentinel-2", temporal={"max_nominal_revisit_days": 1})
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL401"]
    assert outcome.findings[0].capability == {
        "nominal_revisit_days": 5,
        "scope": "equator_constellation_nominal",
    }


@pytest.mark.parametrize(
    ("mission_id", "days"),
    [
        ("sentinel-2", 5),
        ("sentinel-1-iw", 6),
        ("landsat-8", 16),
        ("landsat-9", 16),
        ("landsat-8-9", 8),
    ],
)
def test_nominal_revisit_exactly_meets_requirement(result, codes, mission_id, days):
    outcome = result(mission_id, temporal={"max_nominal_revisit_days": days})
    assert outcome.verdict == PASS
    assert codes(outcome) == ["EFL402"]


def test_efl402_is_informational_and_never_escalates(result):
    """A met revisit requirement records a caveat but keeps the verdict at PASS."""
    outcome = result("sentinel-2", temporal={"max_nominal_revisit_days": 10})
    finding = outcome.findings[0]
    assert finding.code == "EFL402"
    assert finding.effect == PASS
    assert outcome.verdict == PASS
    assert "not equivalent to guaranteed" in finding.message


def test_no_temporal_requirement_produces_no_temporal_finding(result, codes):
    outcome = result("sentinel-2", spectral_bands_all_of=["visible"])
    assert codes(outcome) == []


def test_combined_landsat_is_faster_than_either_satellite(result):
    assert result("landsat-8", temporal={"max_nominal_revisit_days": 8}).verdict == FAIL
    assert result("landsat-8-9", temporal={"max_nominal_revisit_days": 8}).verdict == PASS


def test_temporal_findings_cite_sources(result):
    outcome = result("landsat-8", temporal={"max_nominal_revisit_days": 5})
    assert outcome.findings[0].source_ids
