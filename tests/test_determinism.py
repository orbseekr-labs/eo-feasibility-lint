"""Determinism and offline guarantees.

The same input plus the same catalog and ruleset versions must always produce
byte-identical output, in this process and in a fresh one.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

import pytest
import yaml

from conftest import EXAMPLES_DIR, REPO_ROOT, make_document
from eo_feasibility_lint import loader, render
from eo_feasibility_lint.cli import main

FORBIDDEN_PATTERNS = {
    "iso timestamp": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}",
    "absolute posix path": r'"\s*/(?:Users|home|tmp|var)/',
    "windows path": r"[A-Za-z]:\\\\",
    "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
}

RICH_DOCUMENT = make_document(
    name="determinism-probe",
    missions=["landsat-8-9", "sentinel-2", "sentinel-1-iw"],
    modality_any_of=["optical_multispectral", "sar_c_band"],
    spectral_bands_all_of=["visible", "nir", "thermal_ir"],
    spatial={"optical_max_gsd_m": 10, "sar_max_resolution_m": 10},
    temporal={"max_nominal_revisit_days": 5},
    illumination={"must_support_night": True},
    weather={"must_support_all_weather": True},
    coverage={"min_single_pass_swath_km": 300},
    output="business_metric",
)


@pytest.fixture
def probe_file(tmp_path):
    path = tmp_path / "probe.yaml"
    path.write_text(yaml.safe_dump(RICH_DOCUMENT, sort_keys=False), encoding="utf-8")
    return str(path)


def capture(*argv):
    stdout = io.StringIO()
    main(list(argv), stdout=stdout, stderr=io.StringIO())
    return stdout.getvalue()


def test_json_output_is_repeatable(probe_file):
    assert capture("check", probe_file, "--format", "json") == capture(
        "check", probe_file, "--format", "json"
    )


def test_text_output_is_repeatable(probe_file):
    assert capture("check", probe_file) == capture("check", probe_file)


def test_output_is_stable_across_processes_and_hash_seeds(probe_file):
    """A different PYTHONHASHSEED must not reorder anything."""
    outputs = []
    for seed in ("0", "12345"):
        environment = dict(
            os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(REPO_ROOT / "src")
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "eo_feasibility_lint.cli",
                "check",
                probe_file,
                "--format",
                "json",
            ],
            capture_output=True,
            cwd=REPO_ROOT,
            env=environment,
            check=False,
        )
        outputs.append(completed.stdout)
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("label", sorted(FORBIDDEN_PATTERNS))
def test_json_report_carries_no_environment_data(probe_file, label):
    output = capture("check", probe_file, "--format", "json")
    assert re.search(FORBIDDEN_PATTERNS[label], output) is None


def test_json_report_does_not_leak_the_input_path(tmp_path, probe_file):
    output = capture("check", probe_file, "--format", "json")
    assert str(tmp_path) not in output
    assert probe_file not in output


def test_report_records_the_versions_it_was_produced_with(probe_file):
    report = json.loads(capture("check", probe_file, "--format", "json"))
    assert report["ruleset_version"] == "0.1.0"
    assert report["catalog_version"] == "2026-08-15.1"
    assert report["schema_version"] == "0.1"


def test_finding_order_is_independent_of_rule_execution_order(report):
    outcome = report(
        missions=["sentinel-2"],
        modality_any_of=["sar_c_band"],
        spectral_bands_all_of=["visible", "thermal_ir"],
        temporal={"max_nominal_revisit_days": 1},
        coverage={"min_single_pass_swath_km": 400},
        output="derived_product",
    )
    codes = [finding.code for finding in outcome.mission_results[0].findings]
    assert codes == sorted(codes)


def test_repeated_reason_codes_are_individually_distinguishable(result):
    """A code names a finding TYPE. Repeats must be told apart by their payloads."""
    outcome = result(
        "sentinel-2",
        spectral_bands_all_of=["thermal_ir", "c_band_sar", "panchromatic"],
    )
    repeated = [f for f in outcome.findings if f.code == "EFL202"]
    assert len(repeated) == 3
    payloads = [json.dumps(f.required, sort_keys=True) for f in repeated]
    assert len(set(payloads)) == 3
    assert [f.capability["band_family"] for f in repeated] == [
        "c_band_sar",
        "panchromatic",
        "thermal_ir",
    ]


def test_scope_notice_is_text_only_and_never_reaches_json(probe_file):
    """The closing notice is informational: it must not touch JSON semantics."""
    text = capture("check", probe_file)
    assert render.SCOPE_NOTICE.split(".")[0] in text.replace("\n", " ")

    payload = capture("check", probe_file, "--format", "json")
    assert "PASS is not a guarantee" not in payload
    report = json.loads(payload)
    assert list(report) == [
        "schema_version",
        "ruleset_version",
        "catalog_version",
        "requirement",
        "portfolio_verdict",
        "mission_results",
    ]


def test_scope_notice_does_not_affect_verdicts(probe_file):
    report = json.loads(capture("check", probe_file, "--format", "json"))
    assert report["portfolio_verdict"] == "FAIL"
    assert all(
        finding["code"] != "SCOPE_NOTICE"
        for mission in report["mission_results"]
        for finding in mission["findings"]
    )


def test_repeated_findings_of_one_code_have_a_stable_order(result):
    first = result(
        "sentinel-2",
        spectral_bands_all_of=["thermal_ir", "c_band_sar", "panchromatic"],
    )
    second = result(
        "sentinel-2",
        spectral_bands_all_of=["thermal_ir", "c_band_sar", "panchromatic"],
    )
    assert [f.capability for f in first.findings] == [f.capability for f in second.findings]


@pytest.mark.parametrize(
    "filename",
    [
        "sentinel2-ndvi.yaml",
        "impossible-thermal-sentinel2.yaml",
        "sentinel1-all-weather.yaml",
        "landsat-night-thermal.yaml",
        "business-metric.yaml",
    ],
)
def test_examples_render_repeatably(filename):
    path = str(EXAMPLES_DIR / filename)
    assert capture("check", path) == capture("check", path)
    assert capture("check", path, "--format", "json") == capture(
        "check", path, "--format", "json"
    )


# --- Offline guarantees ---------------------------------------------------


def test_no_network_client_is_imported():
    """The runtime must not reach the network, so it must not import a client."""
    banned = {"requests", "httpx", "urllib.request", "socket", "http.client"}
    sources = list((REPO_ROOT / "src").rglob("*.py"))
    assert sources
    for path in sources:
        text = path.read_text(encoding="utf-8")
        for module in banned:
            assert f"import {module}" not in text, f"{path.name} imports {module}"


def test_yaml_is_only_ever_loaded_safely():
    """Only the strict SafeLoader subclass may parse YAML anywhere in the runtime."""
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "yaml.unsafe_load" not in text, path.name
        assert "yaml.full_load" not in text, path.name
        for line in text.splitlines():
            if "yaml.load(" in line:
                assert "Loader=StrictSafeLoader" in line, f"{path.name}: {line.strip()}"

    assert issubclass(loader.StrictSafeLoader, yaml.SafeLoader)


def test_unsafe_yaml_tags_are_rejected_at_runtime():
    with pytest.raises(yaml.YAMLError):
        loader.safe_load_yaml("!!python/object/apply:os.system ['echo pwned']\n")


def test_runtime_has_no_clock_or_randomness():
    """Nothing in the runtime may consult a clock or a random source."""
    banned = ("import datetime", "import time", "import random", "import uuid", "import secrets")
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for statement in banned:
            assert statement not in text, f"{path.name}: {statement}"
    assert render.WRAP_WIDTH > 0
