"""EFL601 - all-weather requirement.

"All-weather" here means only that the mission is not dependent on visible
cloud-free conditions in the way optical and thermal imaging is. It does not
imply that SAR is unaffected by every atmospheric or environmental condition.
"""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import FAIL, Finding


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    if requirement.must_support_all_weather is not True:
        return []
    if mission.all_weather:
        return []
    return [
        Finding(
            code="EFL601",
            effect=FAIL,
            title="All-weather requirement unmet",
            message=(
                "The mission depends on cloud-free conditions in the way optical and "
                "thermal imaging does."
            ),
            required={"must_support_all_weather": True},
            capability={"all_weather": False},
            source_ids=mission.sources_for("all_weather"),
        )
    ]
