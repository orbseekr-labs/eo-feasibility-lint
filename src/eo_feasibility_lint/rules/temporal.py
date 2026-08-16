"""EFL401 / EFL402 - nominal revisit requirements.

EFL402 is informational and carries effect PASS: a met revisit requirement never
escalates a verdict, but the report still records that a nominal revisit interval
is not a guarantee of usable observation frequency at a specific location.
"""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import FAIL, PASS, Finding


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    limit = requirement.max_nominal_revisit_days
    if limit is None:
        return []

    required = {"max_nominal_revisit_days": limit}
    capability = mission.revisit_capability()
    source_ids = mission.sources_for("nominal_revisit")

    if mission.revisit_days > limit:
        return [
            Finding(
                code="EFL401",
                effect=FAIL,
                title="Nominal revisit requirement unmet",
                message="The mission's nominal revisit interval is longer than required.",
                required=required,
                capability=capability,
                source_ids=source_ids,
            )
        ]

    return [
        Finding(
            code="EFL402",
            effect=PASS,
            title="Nominal revisit is not an availability guarantee",
            message=(
                "The nominal revisit interval satisfies the requirement. Nominal "
                "revisit is not equivalent to guaranteed usable observation frequency "
                "at a particular location."
            ),
            required=required,
            capability=capability,
            source_ids=source_ids,
        )
    ]
