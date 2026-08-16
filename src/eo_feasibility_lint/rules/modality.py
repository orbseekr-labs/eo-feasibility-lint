"""EFL201 - required sensing modality availability."""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import FAIL, Finding


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    if not requirement.modality_any_of:
        return []
    if any(mission.has_modality(modality) for modality in requirement.modality_any_of):
        return []
    return [
        Finding(
            code="EFL201",
            effect=FAIL,
            title="Required modality unavailable",
            message=(
                "The mission provides none of the required sensing modalities."
            ),
            required={"modality_any_of": list(requirement.modality_any_of)},
            capability={"modalities": list(mission.modalities)},
            # An absence conclusion cites the source designated as authoritative
            # for the mission's complete modality inventory.
            source_ids=mission.modality_inventory_source_ids,
        )
    ]
