"""Verdict precedence, portfolio aggregation and deterministic ordering."""

from __future__ import annotations

import pytest

from conftest import make_document
from eo_feasibility_lint.aggregate import MissionSelectionError, build_report, resolve_mission_ids
from eo_feasibility_lint.loader import parse_requirement
from eo_feasibility_lint.models import CONDITIONAL, FAIL, PASS, UNKNOWN, best, worst

# --- Precedence -----------------------------------------------------------


def test_mission_precedence_is_worst_finding_wins():
    assert worst([FAIL, CONDITIONAL, CONDITIONAL, CONDITIONAL]) == FAIL
    assert worst([UNKNOWN, CONDITIONAL, CONDITIONAL, CONDITIONAL]) == UNKNOWN
    assert worst([CONDITIONAL, PASS]) == CONDITIONAL
    assert worst([PASS, PASS]) == PASS
    assert worst([]) == PASS


def test_portfolio_precedence_is_best_candidate_wins():
    assert best([FAIL, PASS, FAIL]) == PASS
    assert best([FAIL, CONDITIONAL, UNKNOWN]) == CONDITIONAL
    assert best([FAIL, UNKNOWN]) == UNKNOWN
    assert best([FAIL, FAIL]) == FAIL


def test_one_fail_outranks_many_conditionals(result):
    outcome = result(
        "sentinel-2",
        output="business_metric",
        spectral_bands_all_of=["thermal_ir"],
        illumination={"must_support_night": True},
    )
    assert outcome.verdict == FAIL


# --- Portfolio ------------------------------------------------------------


def test_one_viable_candidate_makes_the_portfolio_pass(report):
    outcome = report(
        missions=["sentinel-2", "sentinel-1-iw", "landsat-8"],
        modality_any_of=["sar_c_band"],
        illumination={"must_support_night": True},
        weather={"must_support_all_weather": True},
    )
    verdicts = {r.mission_id: r.verdict for r in outcome.mission_results}
    assert verdicts == {
        "sentinel-2": FAIL,
        "sentinel-1-iw": PASS,
        "landsat-8": FAIL,
    }
    assert outcome.portfolio_verdict == PASS


def test_portfolio_fails_only_when_every_candidate_fails(report):
    outcome = report(
        missions=["sentinel-2", "landsat-8"],
        modality_any_of=["sar_c_band"],
    )
    assert outcome.portfolio_verdict == FAIL


def test_portfolio_reports_the_best_of_mixed_verdicts(report):
    outcome = report(
        missions=["sentinel-2", "landsat-8"],
        spectral_bands_all_of=["visible"],
        spatial={"optical_max_gsd_m": 10},
        output="model_inference",
    )
    verdicts = {r.mission_id: r.verdict for r in outcome.mission_results}
    assert verdicts == {"sentinel-2": CONDITIONAL, "landsat-8": FAIL}
    assert outcome.portfolio_verdict == CONDITIONAL


# --- Ordering -------------------------------------------------------------


def test_mission_order_follows_input(catalog):
    requirement = parse_requirement(
        make_document(missions=["landsat-9", "sentinel-2", "landsat-8"]),
        catalog.mission_ids(),
    )
    report = build_report(requirement, catalog)
    assert [r.mission_id for r in report.mission_results] == [
        "landsat-9",
        "sentinel-2",
        "landsat-8",
    ]


def test_mission_order_falls_back_to_catalog_order(catalog):
    requirement = parse_requirement(make_document(), catalog.mission_ids())
    report = build_report(requirement, catalog)
    assert tuple(r.mission_id for r in report.mission_results) == catalog.mission_ids()


def test_overrides_replace_candidate_missions(catalog):
    requirement = parse_requirement(
        make_document(missions=["sentinel-2"]), catalog.mission_ids()
    )
    assert resolve_mission_ids(requirement, catalog, ("landsat-8",)) == ("landsat-8",)


def test_repeated_overrides_are_collapsed(catalog):
    requirement = parse_requirement(make_document(), catalog.mission_ids())
    assert resolve_mission_ids(requirement, catalog, ("landsat-8", "landsat-8")) == ("landsat-8",)


def test_unknown_override_is_rejected(catalog):
    requirement = parse_requirement(make_document(), catalog.mission_ids())
    with pytest.raises(MissionSelectionError, match="unknown mission id"):
        resolve_mission_ids(requirement, catalog, ("worldview-3",))


def test_findings_are_ordered_by_ascending_reason_code(result):
    outcome = result(
        "sentinel-2",
        output="business_metric",
        modality_any_of=["sar_c_band"],
        spectral_bands_all_of=["visible", "thermal_ir"],
        temporal={"max_nominal_revisit_days": 1},
        illumination={"must_support_night": True},
        weather={"must_support_all_weather": True},
        coverage={"min_single_pass_swath_km": 400},
    )
    reported = [finding.code for finding in outcome.findings]
    assert reported == sorted(reported)
    assert reported == ["EFL201", "EFL202", "EFL401", "EFL501", "EFL601", "EFL701", "EFL803"]
