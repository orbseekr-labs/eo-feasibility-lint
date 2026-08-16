"""EFL601 - all-weather requirement."""

from __future__ import annotations

import pytest

from eo_feasibility_lint.models import FAIL, PASS

ALL_WEATHER = {"must_support_all_weather": True}


def test_sar_is_all_weather(result, codes):
    outcome = result("sentinel-1-iw", weather=ALL_WEATHER)
    assert outcome.verdict == PASS
    assert codes(outcome) == []


@pytest.mark.parametrize("mission_id", ["sentinel-2", "landsat-8", "landsat-9", "landsat-8-9"])
def test_optical_and_thermal_missions_are_not_all_weather(result, codes, mission_id):
    outcome = result(mission_id, weather=ALL_WEATHER)
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL601"]


def test_no_all_weather_requirement_produces_no_finding(result, codes):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["visible"],
        weather={"must_support_all_weather": False},
    )
    assert codes(outcome) == []


def test_all_weather_claim_is_narrow(result):
    """The message must not claim SAR is immune to every condition."""
    finding = result("sentinel-2", weather=ALL_WEATHER).findings[0]
    assert "cloud-free" in finding.message
    assert finding.source_ids
