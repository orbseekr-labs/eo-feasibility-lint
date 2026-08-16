"""Mission selection and portfolio aggregation.

Candidate missions are alternatives, so the portfolio asks whether at least one
candidate is technically viable: PASS > CONDITIONAL > UNKNOWN > FAIL. That is the
inverse of the per-mission precedence, which is FAIL > UNKNOWN > CONDITIONAL > PASS.
"""

from __future__ import annotations

from .catalog import Catalog
from .engine import evaluate_mission
from .loader import Requirement
from .models import Report, best


class MissionSelectionError(Exception):
    """A requested mission id is not in the v0.1 catalog."""


def resolve_mission_ids(
    requirement: Requirement,
    catalog: Catalog,
    overrides: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Explicit input order when supplied, otherwise catalog order."""
    selected = overrides or requirement.candidate_missions
    if not selected:
        return catalog.mission_ids()

    unknown = [mission_id for mission_id in selected if catalog.get(mission_id) is None]
    if unknown:
        raise MissionSelectionError(
            "unknown mission id(s): "
            + ", ".join(unknown)
            + "; supported: "
            + ", ".join(catalog.mission_ids())
        )

    # Preserve input order, drop repeats.
    ordered: list[str] = []
    for mission_id in selected:
        if mission_id not in ordered:
            ordered.append(mission_id)
    return tuple(ordered)


def build_report(
    requirement: Requirement,
    catalog: Catalog,
    overrides: tuple[str, ...] = (),
) -> Report:
    mission_ids = resolve_mission_ids(requirement, catalog, overrides)
    results = tuple(
        evaluate_mission(requirement, catalog.get(mission_id)) for mission_id in mission_ids
    )
    portfolio_verdict = best([result.verdict for result in results])
    return Report(
        requirement_name=requirement.name,
        catalog_version=catalog.version,
        portfolio_verdict=portfolio_verdict,
        mission_results=results,
    )
