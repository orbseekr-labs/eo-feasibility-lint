"""EFL301 / EFL302 / EFL303 - spatial resolution requirements.

Optical GSD, thermal GSD and SAR resolution are never interchangeable. A
sensor-family-specific spatial requirement against a mission that lacks that
modality is EFL201, not EFL30x.
"""

from __future__ import annotations

from eo_feasibility_lint.models import FAIL, PASS

# --- Optical --------------------------------------------------------------


def test_explicit_family_uses_that_family_resolution(result, codes):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["red_edge"],
        spatial={"optical_max_gsd_m": 10},
    )
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL301"]
    assert outcome.findings[0].capability == {"band_family": "red_edge", "resolution_m": 20}


def test_explicit_family_that_meets_the_requirement_passes(result):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 10},
    )
    assert outcome.verdict == PASS


def test_each_violating_family_is_reported(result, codes):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["visible", "red_edge", "swir"],
        spatial={"optical_max_gsd_m": 10},
    )
    assert codes(outcome) == ["EFL301", "EFL301"]
    families = {finding.capability["band_family"] for finding in outcome.findings}
    assert families == {"red_edge", "swir"}


def test_default_optical_basis_is_explicit_catalog_data(result, catalog):
    """Landsat defaults to 30 m, never to its 15 m panchromatic band."""
    outcome = result("landsat-8", spatial={"optical_max_gsd_m": 15})
    assert outcome.verdict == FAIL
    finding = outcome.findings[0]
    assert finding.code == "EFL301"
    assert finding.capability["basis"] == "default_multispectral_gsd_m"
    assert finding.capability["resolution_m"] == 30
    # The value is read from the catalog field, not derived from the band table.
    assert catalog.get("landsat-8").default_multispectral_gsd_m == 30
    assert finding.capability["resolution_m"] == (
        catalog.get("landsat-8").default_multispectral_gsd_m
    )
    assert finding.source_ids == catalog.get("landsat-8").sources_for(
        "default_multispectral_gsd_m"
    )


def test_default_optical_basis_names_no_band_family(result):
    """The default is a mission-level fact, not a claim about one band."""
    finding = result("sentinel-2", spatial={"optical_max_gsd_m": 5}).findings[0]
    assert finding.code == "EFL301"
    assert "band_family" not in finding.capability
    assert finding.capability["resolution_m"] == 10


def test_panchromatic_can_still_be_required_explicitly(result):
    outcome = result(
        "landsat-8",
        spectral_bands_all_of=["panchromatic"],
        spatial={"optical_max_gsd_m": 15},
    )
    assert outcome.verdict == PASS


def test_optical_requirement_against_sar_only_mission_is_modality_failure(result, codes):
    outcome = result("sentinel-1-iw", spatial={"optical_max_gsd_m": 10})
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL201"]
    assert outcome.findings[0].required["implied_by"] == "spatial.optical_max_gsd_m"


# --- Thermal --------------------------------------------------------------


def test_thermal_requirement_finer_than_landsat_fails(result, codes):
    outcome = result("landsat-8", spatial={"thermal_max_gsd_m": 50})
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL302"]
    assert outcome.findings[0].capability["resolution_m"] == 100


def test_thermal_requirement_met(result):
    assert result("landsat-9", spatial={"thermal_max_gsd_m": 100}).verdict == PASS


def test_thermal_requirement_against_sentinel2_is_modality_failure(result, codes):
    outcome = result("sentinel-2", spatial={"thermal_max_gsd_m": 100})
    assert codes(outcome) == ["EFL201"]
    assert outcome.findings[0].required["modality"] == "thermal_ir"


# --- SAR ------------------------------------------------------------------


def test_sar_uses_the_worse_nominal_dimension(result):
    """max(5 m range, 20 m azimuth) = 20 m. Intentionally conservative."""
    assert result("sentinel-1-iw", spatial={"sar_max_resolution_m": 20}).verdict == PASS


def test_sar_requirement_finer_than_nominal_fails(result, codes):
    outcome = result("sentinel-1-iw", spatial={"sar_max_resolution_m": 10})
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL303"]
    assert outcome.findings[0].capability["compared_resolution_m"] == 20


def test_sar_requirement_against_optical_mission_is_modality_failure(result, codes):
    outcome = result("sentinel-2", spatial={"sar_max_resolution_m": 20})
    assert codes(outcome) == ["EFL201"]
    assert outcome.findings[0].required["modality"] == "sar_c_band"


def test_sar_resolution_is_never_compared_with_optical_gsd(result):
    """A 10 m optical requirement must not be satisfied by Sentinel-1's 5 m range."""
    outcome = result("sentinel-1-iw", spatial={"optical_max_gsd_m": 10})
    assert outcome.verdict == FAIL
    assert outcome.findings[0].code == "EFL201"


# --- Provenance -----------------------------------------------------------


def test_spatial_findings_cite_sources(result):
    for outcome in (
        result("landsat-8", spatial={"optical_max_gsd_m": 10}),
        result("landsat-8", spatial={"thermal_max_gsd_m": 50}),
        result("sentinel-1-iw", spatial={"sar_max_resolution_m": 10}),
    ):
        assert outcome.findings[0].source_ids
