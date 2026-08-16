"""EFL201 - required modality availability."""

from __future__ import annotations

from eo_feasibility_lint.models import FAIL, PASS


def test_available_modality_produces_no_finding(result):
    assert result("sentinel-2", modality_any_of=["optical_multispectral"]).verdict == PASS


def test_missing_modality_fails(result, codes):
    outcome = result("sentinel-2", modality_any_of=["sar_c_band"])
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL201"]


def test_any_of_is_satisfied_by_one_modality(result):
    outcome = result("sentinel-2", modality_any_of=["sar_c_band", "optical_multispectral"])
    assert outcome.verdict == PASS


def test_landsat_provides_both_optical_and_thermal(result):
    assert result("landsat-8", modality_any_of=["thermal_ir"]).verdict == PASS
    assert result("landsat-8", modality_any_of=["optical_multispectral"]).verdict == PASS


def test_finding_cites_sources_and_capability(result):
    finding = result("sentinel-1-iw", modality_any_of=["optical_multispectral"]).findings[0]
    assert finding.code == "EFL201"
    assert finding.source_ids
    assert finding.capability == {"modalities": ["sar_c_band"]}
    assert finding.required == {"modality_any_of": ["optical_multispectral"]}
