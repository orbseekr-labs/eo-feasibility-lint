"""EFL501 / EFL502 - night operation requirements."""

from __future__ import annotations

from eo_feasibility_lint.models import CONDITIONAL, FAIL, PASS

NIGHT = {"must_support_night": True}
DAY = {"must_support_night": False}


def test_sar_supports_night(result, codes):
    outcome = result("sentinel-1-iw", illumination=NIGHT)
    assert outcome.verdict == PASS
    assert codes(outcome) == []


def test_sentinel2_cannot_operate_at_night(result, codes):
    outcome = result("sentinel-2", illumination=NIGHT)
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL501"]


def test_landsat_without_an_explicit_family_falls_back_to_thermal(result, codes):
    """Thermal IR can support night acquisition conditionally; reflected optical cannot."""
    outcome = result("landsat-8", illumination=NIGHT)
    assert outcome.verdict == CONDITIONAL
    assert codes(outcome) == ["EFL502"]
    assert outcome.findings[0].capability["band_family"] == "thermal_ir"


def test_explicit_thermal_family_is_conditional(result, codes):
    outcome = result("landsat-8", spectral_bands_all_of=["thermal_ir"], illumination=NIGHT)
    assert outcome.verdict == CONDITIONAL
    assert codes(outcome) == ["EFL502"]


def test_explicit_reflected_family_is_not_rescued_by_thermal(result, codes):
    outcome = result("landsat-8", spectral_bands_all_of=["visible"], illumination=NIGHT)
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL501"]
    assert outcome.findings[0].capability["band_family"] == "visible"


def test_mixed_explicit_families_report_each_offender(result, codes):
    outcome = result(
        "landsat-8",
        spectral_bands_all_of=["visible", "thermal_ir"],
        illumination=NIGHT,
    )
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL501", "EFL502"]


def test_explicit_modality_narrows_the_candidates(result, codes):
    optical = result("landsat-8", modality_any_of=["optical_multispectral"], illumination=NIGHT)
    assert optical.verdict == FAIL
    assert codes(optical) == ["EFL501"]

    thermal = result("landsat-8", modality_any_of=["thermal_ir"], illumination=NIGHT)
    assert thermal.verdict == CONDITIONAL
    assert codes(thermal) == ["EFL502"]


def test_daytime_requirement_produces_no_finding(result, codes):
    assert codes(result("sentinel-2", illumination=DAY, spectral_bands_all_of=["visible"])) == []


def test_illumination_findings_cite_sources(result):
    assert result("sentinel-2", illumination=NIGHT).findings[0].source_ids
    assert result("landsat-8", illumination=NIGHT).findings[0].source_ids
