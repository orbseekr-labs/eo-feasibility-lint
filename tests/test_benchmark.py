"""Real-world benchmark regression (benchmark/, docs/real-world-validation.md).

The benchmark records what the tool returned for each blind real-world case. These
tests re-run every case offline and require byte-identical JSON, so any change in
behaviour on real-world inputs shows up as an explicit, reviewable diff. They do not
assert that the recorded results are *correct*; the expected labels and the
agreement analysis live in the benchmark file and the validation document.
"""

from __future__ import annotations

import io
import json

import pytest
import yaml

from conftest import REPO_ROOT
from eo_feasibility_lint.cli import main

BENCHMARK_DIR = REPO_ROOT / "benchmark"
BENCHMARK = yaml.safe_load((BENCHMARK_DIR / "real-world-cases.yaml").read_text(encoding="utf-8"))
TESTABLE = [case for case in BENCHMARK["cases"] if case["testable"]]


def run_check(path):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = main(["check", str(path), "--format", "json"], stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_benchmark_has_cases():
    assert len(BENCHMARK["cases"]) == 30
    assert len(TESTABLE) == 25


@pytest.mark.parametrize("case", TESTABLE, ids=[case["id"] for case in TESTABLE])
def test_benchmark_case_reproduces_recorded_output(case):
    code, out, err = run_check(REPO_ROOT / case["input"])
    assert err == ""
    assert code == case["actual"]["exit_code"]
    assert out == (REPO_ROOT / case["actual"]["raw_json"]).read_text(encoding="utf-8")

    report = json.loads(out)
    assert report["portfolio_verdict"] == case["actual"]["portfolio_verdict"]
    assert {
        result["mission_id"]: result["verdict"] for result in report["mission_results"]
    } == case["actual"]["per_mission"]
    assert (
        sorted(
            {
                finding["code"]
                for result in report["mission_results"]
                for finding in result["findings"]
            }
        )
        == case["actual"]["finding_codes"]
    )


@pytest.mark.parametrize("case", TESTABLE, ids=[case["id"] for case in TESTABLE])
def test_benchmark_recorded_match_is_consistent(case):
    expected, actual, match = case["expected"], case["actual"], case["match"]
    assert match["portfolio_verdict"] == (
        expected["portfolio_verdict"] == actual["portfolio_verdict"]
    )
    assert match["per_mission_verdicts"] == (expected["per_mission"] == actual["per_mission"])
