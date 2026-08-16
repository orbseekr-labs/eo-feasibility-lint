"""The 16 mandatory specification test cases (spec section 45).

Each test maps one-to-one onto a numbered case in the frozen specification and
is kept in that order for traceability. Release gate: all of these must be green.
"""

from __future__ import annotations

import io
import json

from conftest import make_document
from eo_feasibility_lint.cli import main
from eo_feasibility_lint.models import CONDITIONAL, FAIL, PASS, SEVERITY, UNKNOWN


def test_case_01_sentinel2_daytime_visible_10m_5day_passes(result, codes):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 10},
        temporal={"max_nominal_revisit_days": 5},
        illumination={"must_support_night": False},
        output="instrument_measurement",
    )
    assert outcome.verdict == PASS
    assert codes(outcome) == ["EFL402"]  # informational only


def test_case_02_sentinel2_thermal_fails(result, codes):
    outcome = result("sentinel-2", spectral_bands_all_of=["thermal_ir"])
    assert outcome.verdict == FAIL
    assert "EFL202" in codes(outcome)


def test_case_03_sentinel2_all_weather_fails(result, codes):
    outcome = result("sentinel-2", weather={"must_support_all_weather": True})
    assert outcome.verdict == FAIL
    assert "EFL601" in codes(outcome)


def test_case_04_sentinel2_night_fails(result, codes):
    outcome = result("sentinel-2", illumination={"must_support_night": True})
    assert outcome.verdict == FAIL
    assert "EFL501" in codes(outcome)


def test_case_05_sentinel2_one_day_revisit_fails(result, codes):
    outcome = result("sentinel-2", temporal={"max_nominal_revisit_days": 1})
    assert outcome.verdict == FAIL
    assert "EFL401" in codes(outcome)


def test_case_06_sentinel1_sar_night_all_weather_passes(result):
    outcome = result(
        "sentinel-1-iw",
        modality_any_of=["sar_c_band"],
        spectral_bands_all_of=["c_band_sar"],
        spatial={"sar_max_resolution_m": 20},
        temporal={"max_nominal_revisit_days": 6},
        illumination={"must_support_night": True},
        weather={"must_support_all_weather": True},
        output="instrument_measurement",
    )
    assert outcome.verdict == PASS


def test_case_07_sentinel1_300km_single_pass_fails(result, codes):
    outcome = result("sentinel-1-iw", coverage={"min_single_pass_swath_km": 300})
    assert outcome.verdict == FAIL
    assert "EFL701" in codes(outcome)


def test_case_08_landsat8_visible_30m_16day_passes(result):
    outcome = result(
        "landsat-8",
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 30},
        temporal={"max_nominal_revisit_days": 16},
        output="instrument_measurement",
    )
    assert outcome.verdict == PASS


def test_case_09_landsat8_visible_10m_fails(result, codes):
    outcome = result(
        "landsat-8",
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 10},
    )
    assert outcome.verdict == FAIL
    assert "EFL301" in codes(outcome)


def test_case_10_landsat_thermal_night_is_conditional(result, codes):
    outcome = result(
        "landsat-8",
        spectral_bands_all_of=["thermal_ir"],
        illumination={"must_support_night": True},
    )
    assert outcome.verdict == CONDITIONAL
    assert codes(outcome) == ["EFL502"]


def test_case_11_landsat89_eight_day_revisit_is_compatible(result, codes):
    outcome = result("landsat-8-9", temporal={"max_nominal_revisit_days": 8})
    assert "EFL401" not in codes(outcome)
    assert outcome.verdict == PASS


def test_case_12_landsat89_five_day_revisit_fails(result, codes):
    outcome = result("landsat-8-9", temporal={"max_nominal_revisit_days": 5})
    assert outcome.verdict == FAIL
    assert "EFL401" in codes(outcome)


def test_case_13_model_inference_is_at_least_conditional(result, codes):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 10},
        output="model_inference",
    )
    assert SEVERITY[outcome.verdict] >= SEVERITY[CONDITIONAL]
    assert "EFL802" in codes(outcome)


def test_case_14_business_metric_is_at_least_conditional(result, codes):
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 10},
        output="business_metric",
    )
    assert SEVERITY[outcome.verdict] >= SEVERITY[CONDITIONAL]
    assert "EFL803" in codes(outcome)


def test_case_15_no_technical_constraint_is_unknown(result, codes):
    outcome = result("sentinel-2", output="instrument_measurement")
    assert outcome.verdict == UNKNOWN
    assert codes(outcome) == ["EFL901"]


def test_case_16_repeated_execution_is_byte_identical(tmp_path):
    import yaml

    path = tmp_path / "requirement.yaml"
    path.write_text(
        yaml.safe_dump(
            make_document(
                missions=["sentinel-2", "landsat-8-9"],
                spectral_bands_all_of=["visible", "nir"],
                spatial={"optical_max_gsd_m": 10},
                temporal={"max_nominal_revisit_days": 5},
                output="model_inference",
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    outputs = []
    for _ in range(2):
        stdout = io.StringIO()
        main(["check", str(path), "--format", "json"], stdout=stdout, stderr=io.StringIO())
        outputs.append(stdout.getvalue())

    assert outputs[0] == outputs[1]
    assert outputs[0].encode("utf-8") == outputs[1].encode("utf-8")
    json.loads(outputs[0])  # still valid JSON
