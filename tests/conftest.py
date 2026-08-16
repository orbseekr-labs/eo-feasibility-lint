"""Shared fixtures.

Tests build requirement documents as plain dicts and push them through the real
validator, so the tests exercise the same path the CLI does.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eo_feasibility_lint.aggregate import build_report
from eo_feasibility_lint.catalog import load_catalog
from eo_feasibility_lint.engine import evaluate_mission
from eo_feasibility_lint.loader import parse_requirement

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
SCHEMAS_DIR = REPO_ROOT / "schemas"


def make_document(
    *,
    name: str = "test-requirement",
    missions: list[str] | None = None,
    output: str = "instrument_measurement",
    **sections,
) -> dict:
    """Build a requirement document. ``sections`` are ``requirements`` entries."""
    document: dict = {
        "schema_version": "0.1",
        "name": name,
        "requirements": {**sections, "output": {"kind": output}},
    }
    if missions is not None:
        document["candidate_missions"] = missions
    return document


@pytest.fixture(scope="session")
def catalog():
    return load_catalog()


@pytest.fixture
def requirement(catalog):
    def _requirement(**kwargs):
        return parse_requirement(make_document(**kwargs), catalog.mission_ids())

    return _requirement


@pytest.fixture
def result(catalog, requirement):
    """Evaluate one requirement against one mission."""

    def _result(mission_id: str, **kwargs):
        return evaluate_mission(requirement(**kwargs), catalog.get(mission_id))

    return _result


@pytest.fixture
def report(catalog, requirement):
    """Evaluate one requirement across its candidate missions."""

    def _report(**kwargs):
        return build_report(requirement(**kwargs), catalog)

    return _report


@pytest.fixture
def codes():
    def _codes(mission_result):
        return [finding.code for finding in mission_result.findings]

    return _codes
