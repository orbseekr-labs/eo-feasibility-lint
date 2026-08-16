"""EFL701 - single-pass swath requirement.

Only single-pass width is evaluated. Mosaicking multiple passes is out of scope
for v0.1.
"""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import FAIL, Finding


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    minimum = requirement.min_single_pass_swath_km
    if minimum is None or mission.swath_km >= minimum:
        return []
    return [
        Finding(
            code="EFL701",
            effect=FAIL,
            title="Single-pass swath requirement unmet",
            message=(
                "The mission's single-pass swath is narrower than required. Combining "
                "multiple passes is not evaluated."
            ),
            required={"min_single_pass_swath_km": minimum},
            capability={"swath_km": mission.swath_km},
            source_ids=mission.sources_for("swath_km"),
        )
    ]
