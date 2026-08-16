"""EFL202 - required spectral band family availability."""

from __future__ import annotations

import pytest

from eo_feasibility_lint.models import FAIL, PASS


def test_available_families_pass(result):
    assert result("sentinel-2", spectral_bands_all_of=["visible", "nir", "swir"]).verdict == PASS


def test_thermal_on_sentinel2_fails(result, codes):
    outcome = result("sentinel-2", spectral_bands_all_of=["thermal_ir"])
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL202"]


def test_all_of_reports_every_missing_family(result, codes):
    outcome = result("sentinel-2", spectral_bands_all_of=["visible", "thermal_ir", "c_band_sar"])
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL202", "EFL202"]
    missing = {finding.capability["band_family"] for finding in outcome.findings}
    assert missing == {"thermal_ir", "c_band_sar"}


@pytest.mark.parametrize("family", ["red_edge", "water_vapor"])
def test_families_absent_from_landsat(result, family):
    assert result("landsat-8", spectral_bands_all_of=[family]).verdict == FAIL


def test_family_absent_from_catalog_entry_still_cites_sources(result):
    """Sentinel-1 does not list coastal_aerosol at all; provenance must survive."""
    outcome = result("sentinel-1-iw", spectral_bands_all_of=["coastal_aerosol"])
    assert outcome.verdict == FAIL
    assert outcome.findings[0].source_ids


def test_panchromatic_is_landsat_only(result):
    assert result("landsat-8", spectral_bands_all_of=["panchromatic"]).verdict == PASS
    assert result("sentinel-2", spectral_bands_all_of=["panchromatic"]).verdict == FAIL
