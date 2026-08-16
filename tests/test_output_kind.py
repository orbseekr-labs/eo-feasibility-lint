"""EFL801 / EFL802 / EFL803 and EFL901 - what the requested output implies."""

from __future__ import annotations

import pytest

from eo_feasibility_lint.models import CONDITIONAL, FAIL, PASS, UNKNOWN

VIABLE = {"spectral_bands_all_of": ["visible"], "spatial": {"optical_max_gsd_m": 10}}


def test_instrument_measurement_adds_nothing(result, codes):
    outcome = result("sentinel-2", output="instrument_measurement", **VIABLE)
    assert outcome.verdict == PASS
    assert codes(outcome) == []


@pytest.mark.parametrize(
    ("kind", "code"),
    [
        ("derived_product", "EFL801"),
        ("model_inference", "EFL802"),
        ("business_metric", "EFL803"),
    ],
)
def test_inference_kinds_are_conditional(result, codes, kind, code):
    outcome = result("sentinel-2", output=kind, **VIABLE)
    assert outcome.verdict == CONDITIONAL
    assert codes(outcome) == [code]


def test_business_metric_is_never_automatically_fail(result):
    outcome = result("sentinel-2", output="business_metric", **VIABLE)
    assert outcome.verdict != FAIL
    message = outcome.findings[0].message
    assert "external inference chain" in message


def test_output_findings_carry_no_mission_provenance(result):
    """These findings depend on no mission capability, so they cite no sources."""
    outcome = result("sentinel-2", output="model_inference", **VIABLE)
    assert outcome.findings[0].source_ids == ()
    assert outcome.findings[0].capability == {}


def test_output_kind_does_not_rescue_a_hard_failure(result, codes):
    outcome = result("sentinel-2", output="model_inference", spectral_bands_all_of=["thermal_ir"])
    assert outcome.verdict == FAIL
    assert codes(outcome) == ["EFL202", "EFL802"]


def test_output_kind_alone_is_not_testable(result, codes):
    """Section 33: the tool must not produce meaningless PASS results."""
    outcome = result("sentinel-2", output="instrument_measurement")
    assert outcome.verdict == UNKNOWN
    assert codes(outcome) == ["EFL901"]


def test_unknown_outranks_conditional(result, codes):
    outcome = result("sentinel-2", output="model_inference")
    assert codes(outcome) == ["EFL802", "EFL901"]
    assert outcome.verdict == UNKNOWN


def test_no_testable_requirements_finding_cites_nothing(result):
    outcome = result("sentinel-2")
    finding = outcome.findings[0]
    assert finding.code == "EFL901"
    assert finding.source_ids == ()
    assert finding.required == {}
    assert finding.capability == {}
