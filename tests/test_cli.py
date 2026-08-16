"""CLI behaviour, exit codes and command output."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys

import pytest
import yaml

from conftest import EXAMPLES_DIR, REPO_ROOT, make_document
from eo_feasibility_lint.cli import (
    EXIT_INTERNAL,
    EXIT_OK,
    EXIT_THRESHOLD_REACHED,
    EXIT_USAGE,
    main,
)


def run(*argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = main(list(argv), stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


@pytest.fixture
def write(tmp_path):
    def _write(document, filename="requirement.yaml"):
        path = tmp_path / filename
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        return str(path)

    return _write


# --- check ----------------------------------------------------------------


def test_check_text_output(write):
    path = write(make_document(missions=["sentinel-2"], spectral_bands_all_of=["visible"]))
    code, out, err = run("check", path)
    assert code == EXIT_OK
    assert err == ""
    assert "EO FEASIBILITY LINT" in out
    assert "Verdict: PASS" in out
    assert "Portfolio verdict:" in out


def test_check_json_output_shape(write):
    path = write(make_document(missions=["sentinel-2"], spectral_bands_all_of=["thermal_ir"]))
    code, out, _ = run("check", path, "--format", "json")
    assert code == EXIT_THRESHOLD_REACHED
    report = json.loads(out)
    assert report["schema_version"] == "0.1"
    assert report["ruleset_version"] == "0.1.0"
    assert report["catalog_version"] == "2026-08-15.1"
    assert report["requirement"] == {"name": "test-requirement"}
    assert report["portfolio_verdict"] == "FAIL"
    assert report["mission_results"][0]["mission_id"] == "sentinel-2"
    assert report["mission_results"][0]["findings"][0]["code"] == "EFL202"


def test_json_report_key_order_is_stable(write):
    path = write(make_document(spectral_bands_all_of=["visible"]))
    _, out, _ = run("check", path, "--format", "json")
    report = json.loads(out)
    assert list(report) == [
        "schema_version",
        "ruleset_version",
        "catalog_version",
        "requirement",
        "portfolio_verdict",
        "mission_results",
    ]
    assert list(report["mission_results"][0]) == ["mission_id", "verdict", "findings"]


def test_mission_option_overrides_candidate_missions(write):
    path = write(make_document(missions=["sentinel-2"], spectral_bands_all_of=["visible"]))
    _, out, _ = run("check", path, "--mission", "landsat-8", "--format", "json")
    report = json.loads(out)
    assert [r["mission_id"] for r in report["mission_results"]] == ["landsat-8"]


def test_mission_option_is_repeatable_and_ordered(write):
    path = write(make_document(spectral_bands_all_of=["visible"]))
    _, out, _ = run(
        "check", path, "--mission", "landsat-9", "--mission", "sentinel-2", "--format", "json"
    )
    report = json.loads(out)
    assert [r["mission_id"] for r in report["mission_results"]] == ["landsat-9", "sentinel-2"]


@pytest.mark.parametrize(
    ("fail_on", "expected"),
    [
        ("fail", EXIT_OK),
        ("unknown", EXIT_OK),
        ("conditional", EXIT_THRESHOLD_REACHED),
    ],
)
def test_fail_on_threshold(write, fail_on, expected):
    path = write(
        make_document(
            missions=["sentinel-2"],
            spectral_bands_all_of=["visible"],
            output="model_inference",
        )
    )
    code, _, _ = run("check", path, "--fail-on", fail_on)
    assert code == expected


def test_fail_on_defaults_to_fail(write):
    path = write(make_document(missions=["sentinel-2"], spectral_bands_all_of=["thermal_ir"]))
    assert run("check", path)[0] == EXIT_THRESHOLD_REACHED


def test_unknown_verdict_reaches_the_unknown_threshold(write):
    path = write(make_document(missions=["sentinel-2"]))
    assert run("check", path, "--fail-on", "unknown")[0] == EXIT_THRESHOLD_REACHED
    assert run("check", path, "--fail-on", "fail")[0] == EXIT_OK


# --- Usage errors ---------------------------------------------------------


def test_missing_file_is_a_usage_error(tmp_path):
    code, _, err = run("check", str(tmp_path / "absent.yaml"))
    assert code == EXIT_USAGE
    assert "cannot be read" in err


def test_invalid_document_is_a_usage_error(write):
    document = make_document()
    document["schema_version"] = "9.9"
    code, out, err = run("check", write(document))
    assert code == EXIT_USAGE
    assert out == ""
    assert "schema_version" in err


def test_unknown_mission_option_is_a_usage_error(write):
    path = write(make_document(spectral_bands_all_of=["visible"]))
    code, _, err = run("check", path, "--mission", "worldview-3")
    assert code == EXIT_USAGE
    assert "unknown mission id" in err


def test_usage_errors_never_look_like_verdicts(write):
    document = make_document()
    document["requirements"]["output"]["kind"] = "revenue"
    code, out, _ = run("check", write(document))
    assert code == EXIT_USAGE
    assert "PASS" not in out and "FAIL" not in out


def test_internal_failure_exit_code_is_distinct():
    assert len({EXIT_OK, EXIT_THRESHOLD_REACHED, EXIT_USAGE, EXIT_INTERNAL}) == 4


# --- Other commands -------------------------------------------------------


def test_list_missions():
    code, out, _ = run("list-missions")
    assert code == EXIT_OK
    for mission_id in ("sentinel-2", "sentinel-1-iw", "landsat-8", "landsat-9", "landsat-8-9"):
        assert mission_id in out
    assert "2026-08-15.1" in out


def test_show_mission():
    code, out, _ = run("show-mission", "sentinel-1-iw")
    assert code == EXIT_OK
    assert "Copernicus Sentinel-1 IW" in out
    assert "5 m range x 20 m azimuth" in out
    assert "https://sentiwiki.copernicus.eu/web/s1-mission" in out
    assert "provenance only" in out


def test_show_mission_reports_night_support():
    _, out, _ = run("show-mission", "landsat-8")
    assert "thermal_ir: 100 m (night: occasional)" in out
    assert "visible: 30 m (night: no)" in out


def test_show_unknown_mission_is_a_usage_error():
    code, _, err = run("show-mission", "worldview-3")
    assert code == EXIT_USAGE
    assert "unknown mission id" in err


def test_rules_lists_every_reason_code():
    code, out, _ = run("rules")
    assert code == EXIT_OK
    for reason_code in (
        "EFL201",
        "EFL202",
        "EFL301",
        "EFL302",
        "EFL303",
        "EFL401",
        "EFL402",
        "EFL501",
        "EFL502",
        "EFL601",
        "EFL701",
        "EFL801",
        "EFL802",
        "EFL803",
        "EFL901",
    ):
        assert reason_code in out
    # EFL902 was removed before release: the schema rejects unmodelled properties.
    assert "EFL902" not in out
    assert "reserved" not in out.lower()


# --- Shipped examples -----------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "expected_verdict"),
    [
        ("sentinel2-ndvi.yaml", "CONDITIONAL"),
        ("impossible-thermal-sentinel2.yaml", "FAIL"),
        ("sentinel1-all-weather.yaml", "PASS"),
        ("landsat-night-thermal.yaml", "CONDITIONAL"),
        ("business-metric.yaml", "CONDITIONAL"),
    ],
)
def test_examples_produce_their_documented_verdicts(filename, expected_verdict):
    _, out, _ = run("check", str(EXAMPLES_DIR / filename), "--format", "json")
    assert json.loads(out)["portfolio_verdict"] == expected_verdict


def test_definition_of_done_example_explains_itself():
    """A new user must see what failed, why, and which specification supports it."""
    code, out, _ = run("check", str(EXAMPLES_DIR / "impossible-thermal-sentinel2.yaml"))
    assert code == EXIT_THRESHOLD_REACHED
    assert "Verdict: FAIL" in out
    assert "EFL202 FAIL" in out
    assert "thermal_ir not available" in out
    assert "esa-sentiwiki-s2-mission" in out
    # ...and what the tool did not evaluate.
    assert "PASS is not a guarantee" in out
    assert "were not evaluated" in out


def test_every_text_report_states_what_was_not_evaluated(write):
    path = write(make_document(missions=["sentinel-1-iw"], spectral_bands_all_of=["c_band_sar"]))
    code, out, _ = run("check", path)
    assert code == EXIT_OK
    assert "Verdict: PASS" in out
    assert "PASS is not a guarantee that a real EO project will succeed." in out


# --- Module entry point ---------------------------------------------------


def test_module_entry_point_runs():
    completed = subprocess.run(
        [sys.executable, "-m", "eo_feasibility_lint.cli", "list-missions"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src")),
        check=False,
    )
    assert completed.returncode == EXIT_OK
    assert "sentinel-2" in completed.stdout
