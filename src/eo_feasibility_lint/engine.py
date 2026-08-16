"""The rule engine: one requirement against one mission.

Rules run in a fixed order and each one is an independent deterministic unit.
The engine adds no judgement of its own beyond precedence and ordering.
"""

from __future__ import annotations

from .catalog import Mission
from .loader import Requirement
from .models import UNKNOWN, Finding, MissionResult, worst
from .rules import CAPABILITY_RULES, output_kind


def no_testable_requirements_finding() -> Finding:
    """EFL901. Depends on no mission capability, so it cites no sources."""
    return Finding(
        code="EFL901",
        effect=UNKNOWN,
        title="No testable requirements",
        message=(
            "No technical requirement that v0.1 knows how to evaluate was supplied, "
            "so feasibility cannot be determined. A meaningless PASS is not produced."
        ),
        required={},
        capability={},
        source_ids=(),
    )


def evaluate_mission(requirement: Requirement, mission: Mission) -> MissionResult:
    findings: list[Finding] = []

    if requirement.has_testable_requirements():
        for rule in CAPABILITY_RULES:
            findings.extend(rule.evaluate(requirement, mission))
    else:
        findings.append(no_testable_requirements_finding())

    findings.extend(output_kind.evaluate(requirement, mission))
    findings.sort(key=Finding.sort_key)

    verdict = worst([finding.effect for finding in findings])
    return MissionResult(mission_id=mission.id, verdict=verdict, findings=tuple(findings))
